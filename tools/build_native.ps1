param([switch]$Build)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceRoot = Join-Path $projectRoot 'native/.horizon-source'
$mixinsRoot = Join-Path $projectRoot 'native/.mixins-source'
$bundleRoot = Join-Path $projectRoot 'native/mixins'
$horizonRevision = '36eb98b6f6ec4f22649cbe65bbfd32bc0dc2083f'
$mixinsRevision = '5a64af938ec86b00d53d16a408aabc0038fb3e57'

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program exited with $LASTEXITCODE" }
}

foreach ($repo in @(
    @{ Path = $sourceRoot; Url = 'https://github.com/horizon-rust/horizon'; Revision = $horizonRevision },
    @{ Path = $mixinsRoot; Url = 'https://github.com/horizon-rust/horizon-mixins'; Revision = $mixinsRevision }
)) {
    if (-not (Test-Path -LiteralPath $repo.Path)) {
        Invoke-Checked git @('clone', $repo.Url, $repo.Path)
    }
    $actualRevision = & git -C $repo.Path rev-parse HEAD
    if ($actualRevision -ne $repo.Revision) {
        Invoke-Checked git @('-C', $repo.Path, 'fetch', 'origin', $repo.Revision)
        Invoke-Checked git @('-C', $repo.Path, 'checkout', '--detach', $repo.Revision)
    }
}

Push-Location $projectRoot
try {
    Invoke-Checked python @('native/tools/generate.py')
    Invoke-Checked cargo @('test', '--manifest-path', 'native/Cargo.toml')
    $bundleHashes = Get-ChildItem -LiteralPath $bundleRoot -Recurse -File |
        Sort-Object FullName | Get-FileHash -Algorithm SHA256
    $bundleBytes = [Text.Encoding]::UTF8.GetBytes(($bundleHashes.Hash -join ''))
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $bundleDigest = [BitConverter]::ToString($sha.ComputeHash($bundleBytes)).Replace('-', '').Substring(0, 16).ToLowerInvariant() }
    finally { $sha.Dispose() }
    # The pinned mixin tool requires fresh output for changed bundles on Windows.
    $stagedRoot = Join-Path $projectRoot "native/target/stages/$bundleDigest"
    Push-Location $mixinsRoot
    try { Invoke-Checked cargo @('build', '--locked', '-p', 'horizon-mixins-cli') }
    finally { Pop-Location }
    Push-Location $sourceRoot
    try { Invoke-Checked cargo @('fetch', '--locked') }
    finally { Pop-Location }
    $mixinExe = Join-Path $mixinsRoot 'target/debug/horizon-mixins.exe'
    $previousOffline = $env:CARGO_NET_OFFLINE
    try {
        $env:CARGO_NET_OFFLINE = 'true'
        Invoke-Checked $mixinExe @('apply', '--workspace', $sourceRoot, '--mods', (Join-Path $projectRoot 'native/mixins'), '--out', $stagedRoot)
    }
    finally { $env:CARGO_NET_OFFLINE = $previousOffline }
    Push-Location $stagedRoot
    $previousTarget = $env:CARGO_TARGET_DIR
    try {
        $env:CARGO_TARGET_DIR = Join-Path $projectRoot 'native/target/build'
        $operation = if ($Build) { 'build' } else { 'check' }
        Invoke-Checked cargo @($operation, '--locked', '-p', 'horizon-client', '--no-default-features')
    }
    finally {
        $env:CARGO_TARGET_DIR = $previousTarget
        Pop-Location
    }
}
finally { Pop-Location }
