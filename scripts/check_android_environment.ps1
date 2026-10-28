param(
    [string]$SdkPath,
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $projectRoot 'reports/preflight-2026-10-28'
}

function Get-ChildNames([string]$Path) {
    if (Test-Path -LiteralPath $Path -PathType Container) {
        return @(Get-ChildItem -LiteralPath $Path -Directory | Select-Object -ExpandProperty Name)
    }
    return @()
}

function Invoke-ReadOnlyProbe([string]$Executable, [string]$Arguments) {
    # Java writes a successful version response to stderr. Capture both streams
    # directly so Windows PowerShell 5.1 does not treat that as a terminating error.
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $Executable
    $startInfo.Arguments = $Arguments
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    try {
        [void]$process.Start()
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $combined = $stdoutTask.Result + "`n" + $stderrTask.Result
        return [pscustomobject]@{
            exitCode = $process.ExitCode
            lines = @($combined -split '\r?\n' | Where-Object { $_.Trim() })
        }
    }
    finally { $process.Dispose() }
}

# USERPROFILE avoids a sandbox-specific LOCALAPPDATA redirect being mistaken for a missing SDK.
$sdkCandidates = @($SdkPath, $env:ANDROID_HOME, $env:ANDROID_SDK_ROOT,
    (Join-Path $env:USERPROFILE 'AppData/Local/Android/Sdk')) |
    Where-Object { $_ } | Select-Object -Unique
$resolvedSdk = $sdkCandidates | Where-Object {
    Test-Path -LiteralPath (Join-Path $_ 'platforms') -PathType Container
} | Select-Object -First 1

$javaCommand = Get-Command java -ErrorAction SilentlyContinue
$javaVersion = @()
$javaExitCode = $null
if ($javaCommand) {
    $javaProbe = Invoke-ReadOnlyProbe $javaCommand.Source '-version'
    $javaVersion = @($javaProbe.lines)
    $javaExitCode = $javaProbe.exitCode
}

$jdkHomes = @()
$adoptium = 'C:/Program Files/Eclipse Adoptium'
if (Test-Path -LiteralPath $adoptium) {
    $jdkHomes = @(Get-ChildItem -LiteralPath $adoptium -Directory |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'bin/java.exe') } |
        Select-Object -ExpandProperty FullName)
}

$studioInfo = @()
foreach ($studioPath in @('D:/Program Files (x86)/Android Studio', 'F:/Program Files (x86)/Android Studio')) {
    $infoPath = Join-Path $studioPath 'product-info.json'
    if (Test-Path -LiteralPath $infoPath) {
        $info = Get-Content -LiteralPath $infoPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $studioInfo += [ordered]@{ path = $studioPath; version = $info.version; buildNumber = $info.buildNumber }
    }
}

$gradlePaths = @(Resolve-Path -Path (Join-Path $env:USERPROFILE '.gradle/wrapper/dists/gradle-*/*/gradle-*/bin/gradle.bat') -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty Path)
$platforms = @()
$buildTools = @()
$systemImages = @()
$avds = @()
$adbVersion = @()
$hasCommandLineTools = $false
if ($resolvedSdk) {
    $platforms = @(Get-ChildNames (Join-Path $resolvedSdk 'platforms'))
    $buildTools = @(Get-ChildNames (Join-Path $resolvedSdk 'build-tools'))
    $systemImages = @(Get-ChildNames (Join-Path $resolvedSdk 'system-images'))
    $hasCommandLineTools = Test-Path -LiteralPath (Join-Path $resolvedSdk 'cmdline-tools')
    $adbPath = Join-Path $resolvedSdk 'platform-tools/adb.exe'
    if (Test-Path -LiteralPath $adbPath) {
        $adbProbe = Invoke-ReadOnlyProbe $adbPath 'version'
        $adbVersion = @($adbProbe.lines)
    }
    $emulatorPath = Join-Path $resolvedSdk 'emulator/emulator.exe'
    if (Test-Path -LiteralPath $emulatorPath) {
        $avdProbe = Invoke-ReadOnlyProbe $emulatorPath '-list-avds'
        $avds = @($avdProbe.lines)
    }
}

$report = [ordered]@{
    checkedAt = (Get-Date -Format o)
    projectRoot = $projectRoot
    project = [ordered]@{
        gitInitialized = (Test-Path -LiteralPath (Join-Path $projectRoot '.git'))
        gradleWrapperPresent = (Test-Path -LiteralPath (Join-Path $projectRoot 'gradlew.bat'))
        androidManifestPresent = (Test-Path -LiteralPath (Join-Path $projectRoot 'app/src/main/AndroidManifest.xml'))
    }
    java = [ordered]@{ effectiveHome = $env:JAVA_HOME; executable = $(if ($javaCommand) { $javaCommand.Source } else { $null }); version = $javaVersion; probeExitCode = $javaExitCode; installedHomes = $jdkHomes }
    androidStudio = $studioInfo
    sdk = [ordered]@{
        path = $resolvedSdk; platforms = $platforms; buildTools = $buildTools
        systemImages = $systemImages; commandLineToolsPresent = $hasCommandLineTools
        sdk37Present = ($platforms -contains 'android-37')
        androidHomeConfigured = [bool]$env:ANDROID_HOME; androidSdkRootConfigured = [bool]$env:ANDROID_SDK_ROOT
    }
    cachedGradleExecutables = $gradlePaths
    adbVersion = $adbVersion
    avds = $avds
    limits = @('Read-only environment inventory; no downloads or environment changes.',
        'No APK build, device connection, emulator boot, signing or installation test performed.',
        'Cached Gradle inventory does not prove compatibility with the selected dependency versions.')
}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$outputPath = Join-Path $OutputDirectory 'android-environment.json'
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $outputPath -Encoding UTF8
Write-Output "Environment inventory saved: $outputPath"
Write-Output "SDK 37 installed: $($report.sdk.sdk37Present); Android project present: $($report.project.androidManifestPresent)"
