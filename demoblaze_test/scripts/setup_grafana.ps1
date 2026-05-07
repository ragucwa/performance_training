param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$PgHost = "localhost",
    [string]$PgPort = "5432",
    [string]$PgUser = "postgres",
    [string]$PgPassword = "password",
    [string[]]$DashboardIds = @("10878", "14423", "14422", "15419")
)

$pair = "admin:admin"
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{ Authorization = "Basic $auth"; Accept = "application/json"; "Content-Type" = "application/json" }
$datasourceName = "locust_timescale"

for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        Invoke-RestMethod -Method Get -Uri "$GrafanaUrl/api/health" -Headers $headers | Out-Null
        break
    } catch {
        if ($attempt -eq 29) {
            throw
        }

        Start-Sleep -Seconds 2
    }
}

$datasource = @{
    access = "proxy"
    basicAuth = $false
    basicAuthPassword = ""
    basicAuthUser = ""
    database = "postgres"
    isDefault = $false
    jsonData = @{
        postgresVersion = 1200
        sslmode = "disable"
        timescaledb = $true
    }
    name = $datasourceName
    orgId = 1
    readOnly = $false
    secureJsonData = @{
        password = $PgPassword
    }
    type = "postgres"
    url = "$PgHost`:$PgPort"
    user = $PgUser
    version = 3
    withCredentials = $false
} | ConvertTo-Json -Depth 6

function Get-ErrorResponseBody {
    param([System.Management.Automation.ErrorRecord]$ErrorRecord)

    $response = $ErrorRecord.Exception.Response
    if (-not $response) {
        return ""
    }

    try {
        $stream = $response.GetResponseStream()
        if (-not $stream) {
            return ""
        }

        $reader = New-Object System.IO.StreamReader($stream)
        $body = $reader.ReadToEnd()
        $reader.Dispose()
        $stream.Dispose()
        return $body
    } catch {
        return ""
    }
}

$existingDatasource = $null

try {
    $existingDatasource = Invoke-RestMethod -Method Get -Uri "$GrafanaUrl/api/datasources/name/$datasourceName" -Headers $headers
} catch {
    $responseBody = Get-ErrorResponseBody $_
    if ($responseBody -and -not $responseBody.Contains("not found")) {
        throw
    }
}

if (-not $existingDatasource) {
    try {
        Invoke-RestMethod -Method Post -Uri "$GrafanaUrl/api/datasources" -Headers $headers -Body $datasource | Out-Null
    } catch {
        $responseBody = Get-ErrorResponseBody $_
        if (-not $responseBody.Contains("already exists")) {
            throw
        }
    }
}

foreach ($dashboardId in $DashboardIds) {
    $dashboard = Invoke-RestMethod -Method Get -Uri "$GrafanaUrl/api/gnet/dashboards/$dashboardId" -Headers $headers
    $payload = @{
        dashboard = $dashboard.json
        overwrite = $true
        inputs = @(
            @{
                name = "DS_LOCUST"
                type = "datasource"
                pluginId = "postgres"
                value = $datasourceName
            }
        )
    } | ConvertTo-Json -Depth 20

    Invoke-RestMethod -Method Post -Uri "$GrafanaUrl/api/dashboards/import" -Headers $headers -Body $payload | Out-Null
}

Write-Host "Grafana is ready at $GrafanaUrl/d/qjIIww4Zz?from=now-15m&to=now"