# Code Signing Setup Guide

## Current Status
✅ **SignTool Detection**: Working - Found in Windows SDK  
✅ **Certificate Creation**: Created self-signed certificate  
⚠️ **Certificate Trust**: Needs to be installed to trusted store  
❌ **Signing Process**: Failing with internal error (0x8007000b)

## Quick Setup (Self-Signed for Development)

### Option 1: Fix Current Self-Signed Certificate

Run PowerShell as Administrator and execute:

```powershell
# Import certificate to trusted root store
$password = ConvertTo-SecureString -String "PDFUtility2025" -Force -AsPlainText
Import-PfxCertificate -FilePath "d:\PDFUtility\certificate.pfx" -CertStoreLocation "Cert:\LocalMachine\Root" -Password $password

# Also import to Trusted Publishers
Import-PfxCertificate -FilePath "d:\PDFUtility\certificate.pfx" -CertStoreLocation "Cert:\LocalMachine\TrustedPublisher" -Password $password
```

### Option 2: Create New Code Signing Certificate (Recommended)

Run PowerShell as Administrator:

```powershell
# Create a proper code signing certificate
$cert = New-SelfSignedCertificate -Type CodeSigning -Subject "CN=PDF Utility Developer" -KeyUsage DigitalSignature -KeyAlgorithm RSA -KeyLength 2048 -Provider "Microsoft Enhanced RSA and AES Cryptographic Provider" -CertStoreLocation "Cert:\CurrentUser\My" -NotAfter (Get-Date).AddYears(3)

# Export to PFX with password
$password = ConvertTo-SecureString -String "PDFUtility2025" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath "d:\PDFUtility\certificate.pfx" -Password $password

# Install to trusted root store
Import-PfxCertificate -FilePath "d:\PDFUtility\certificate.pfx" -CertStoreLocation "Cert:\LocalMachine\Root" -Password $password
Import-PfxCertificate -FilePath "d:\PDFUtility\certificate.pfx" -CertStoreLocation "Cert:\LocalMachine\TrustedPublisher" -Password $password

echo "✅ Code signing certificate setup complete!"
```

## Configuration Options

### Environment Variables (Recommended for CI/CD)
```batch
set CERT_PATH=d:\PDFUtility\certificate.pfx
set CERT_PASSWORD=PDFUtility2025
```

### Direct File Placement (Current Setup)
- Place `certificate.pfx` in project root: `d:\PDFUtility\certificate.pfx`
- Password: `PDFUtility2025` (automatically detected)

## Production Setup (Real Certificate)

For production releases, you'll need a real code signing certificate from a Certificate Authority:

1. **Purchase from CA**: Sectigo, DigiCert, GlobalSign, etc. (~$200-500/year)
2. **Place certificate**: Save as `certificate.pfx` or set `CERT_PATH`
3. **Set password**: Set `CERT_PASSWORD` environment variable
4. **Test signing**: Run `py BuildSystem/build_cli.py --start package`

## Troubleshooting

### Common Issues:

1. **Error 0x8007000b**: Certificate not trusted
   - Solution: Import to Root and TrustedPublisher stores

2. **Access Denied**: Need admin rights
   - Solution: Run PowerShell as Administrator

3. **Certificate Chain Issues**: Self-signed not in trusted store
   - Solution: Follow Option 2 above

4. **Timestamp Server Issues**: Network problems
   - Solution: Will be handled gracefully (signature still valid)

## Testing

After setup, test with:
```bash
cd d:\PDFUtility
py BuildSystem/build_cli.py --start package
```

Look for:
```
✅ Package signed successfully
```

## Alternative: Skip Signing

To disable signing completely, rename or delete `certificate.pfx`:
```bash
mv certificate.pfx certificate.pfx.disabled
```

The build will complete without signing (suitable for development).
