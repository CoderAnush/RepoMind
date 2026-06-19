output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.cdn.domain_name
  description = "The domain name of the CloudFront CDN distribution"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.frontend.bucket
  description = "The name of the static hosting S3 bucket"
}
