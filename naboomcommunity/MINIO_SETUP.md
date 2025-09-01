# MinIO Storage Configuration

## Overview
Your Django application is now configured to use MinIO for file storage. This replaces the local file system storage with S3-compatible object storage.

## Configuration

### Environment Variables
Set these environment variables to configure your MinIO connection:

```bash
# MinIO Server Details
export AWS_S3_ENDPOINT_URL="http://your-minio-server:9000"
export AWS_S3_CUSTOM_DOMAIN="your-minio-server:9000"
export AWS_S3_USE_SSL="False"
export AWS_S3_VERIFY="False"

# MinIO Credentials
export AWS_ACCESS_KEY_ID="minioadmin"
export AWS_SECRET_ACCESS_KEY="minioadmin"

# Bucket Configuration
export AWS_STORAGE_BUCKET_NAME="naboomcommunity"
export AWS_S3_REGION_NAME="us-east-1"
```

### Default Configuration
If no environment variables are set, the following defaults are used:
- **Endpoint**: `http://localhost:9000`
- **Credentials**: `minioadmin` / `minioadmin`
- **Bucket**: `naboomcommunity`
- **SSL**: Disabled
- **Region**: `us-east-1`

## Setup Steps

### 1. Start MinIO Server
Make sure your MinIO server is running and accessible.

### 2. Create Bucket
Run the setup command to create the required bucket:
```bash
python manage.py setup_minio
```

### 3. Collect Static Files
Upload static files to MinIO:
```bash
python manage.py collectstatic
```

## File Storage

### Static Files
- **Local Path**: `/static/`
- **MinIO Path**: `{bucket}/static/`
- **URL**: `{endpoint}/{bucket}/static/`

### Media Files
- **Local Path**: `/media/`
- **MinIO Path**: `{bucket}/media/`
- **URL**: `{endpoint}/{bucket}/media/`

## Management Commands

### Setup MinIO
```bash
python manage.py setup_minio
```
Creates the required bucket and folder structure.

### Custom Bucket Name
```bash
python manage.py setup_minio --bucket-name my-custom-bucket
```

## Troubleshooting

### Connection Issues
1. Verify MinIO server is running
2. Check endpoint URL and port
3. Ensure credentials are correct
4. Verify network connectivity

### Permission Issues
1. Check MinIO bucket policies
2. Verify AWS credentials have proper permissions
3. Ensure bucket exists and is accessible

### File Upload Issues
1. Check bucket exists
2. Verify write permissions
3. Check file size limits
4. Review MinIO server logs

## Production Considerations

### Security
- Use strong credentials
- Enable SSL/TLS in production
- Set up proper bucket policies
- Use IAM roles if possible

### Performance
- Consider CDN integration
- Optimize file sizes
- Use appropriate storage classes
- Monitor usage and costs

### Backup
- Set up MinIO backup strategies
- Consider cross-region replication
- Implement versioning if needed
