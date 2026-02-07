param(
    [Parameter(Mandatory = $true)]
    [string]$Port,

    [int]$Baud = 115200
)

$serial = New-Object System.IO.Ports.SerialPort $Port, $Baud, 'None', 8, 'One'
$serial.NewLine = ";"
$serial.ReadTimeout = 1000
$serial.WriteTimeout = 1000

try {
    $serial.Open()

    function Send-Cat($cmd) {
        Write-Host "=> $cmd" -ForegroundColor Cyan
        $serial.Write($cmd + ";")
        Start-Sleep -Milliseconds 50
        $response = $serial.ReadExisting()
        if ($response) {
            Write-Host "<= $response" -ForegroundColor Green
        } else {
            Write-Host "<= (no response)" -ForegroundColor Yellow
        }
    }

    Send-Cat "ID"
    Send-Cat "FA"
    Send-Cat "FA00014075000"
    Send-Cat "FA"
    Send-Cat "FB"
    Send-Cat "FB00007074000"
    Send-Cat "FB"
    Send-Cat "MD"
    Send-Cat "MD2"
    Send-Cat "IF"
    Send-Cat "AG128"
    Send-Cat "RG128"
    Send-Cat "SM"
    Send-Cat "GT2"
    Send-Cat "KS020"
    Send-Cat "KYTEST"
    Send-Cat "TX1"
    Send-Cat "RX"
}
finally {
    if ($serial.IsOpen) {
        $serial.Close()
    }
}
