param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Command,
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $root "bootstrap.py") -- $Command @Arguments
exit $LASTEXITCODE