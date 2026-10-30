param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$GradleArguments
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$javaCandidates = @(
    $env:YUNO_JAVA_HOME,
    'C:/Program Files/Eclipse Adoptium/jdk-21.0.9.10-hotspot'
)
$javaHome = $javaCandidates | Where-Object {
    $_ -and (Test-Path -LiteralPath (Join-Path $_ 'bin/java.exe'))
} | Select-Object -First 1
if (-not $javaHome) {
    throw 'Set YUNO_JAVA_HOME to a JDK 21 installation for this process.'
}
$oldJavaHome = $env:JAVA_HOME
try {
    $env:JAVA_HOME = $javaHome
    Push-Location -LiteralPath $projectRoot
    try {
        & (Join-Path $projectRoot 'gradlew.bat') @GradleArguments
        $gradleExit = $LASTEXITCODE
    } finally {
        Pop-Location
    }
} finally {
    $env:JAVA_HOME = $oldJavaHome
}
exit $gradleExit
