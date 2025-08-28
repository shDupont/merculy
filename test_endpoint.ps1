# PowerShell script to test the Google login endpoint

$url = "https://merculy-app-hehte6a4ffc5hqeh.brazilsouth-01.azurewebsites.net/api/auth/google-login"
$body = @{
    token = "test_token"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
}

try {
    Write-Host "Testing endpoint: $url" -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri $url -Method POST -Body $body -Headers $headers -ErrorAction Stop
    Write-Host "✅ Success! Response:" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 3) -ForegroundColor Green
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    $statusDescription = $_.Exception.Response.StatusDescription
    
    Write-Host "❌ Error: HTTP $statusCode - $statusDescription" -ForegroundColor Red
    
    if ($statusCode -eq 405) {
        Write-Host "Method Not Allowed - This confirms the endpoint exists but wrong method or URL" -ForegroundColor Red
    }
    elseif ($statusCode -eq 404) {
        Write-Host "Not Found - The endpoint doesn't exist at this URL" -ForegroundColor Red
    }
    elseif ($statusCode -eq 400) {
        Write-Host "Bad Request - This is expected with test token" -ForegroundColor Yellow
    }
    
    # Try to get response body
    try {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body: $responseBody" -ForegroundColor Cyan
    }
    catch {
        Write-Host "Could not read response body" -ForegroundColor Gray
    }
}
