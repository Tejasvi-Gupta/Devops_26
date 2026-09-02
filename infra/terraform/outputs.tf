output "public_ip" {
  description = "The instance's stable public IP (Elastic IP)"
  value       = aws_eip.app.public_ip
}

output "frontend_url" {
  description = "URL to open the dashboard once the app has finished starting"
  value       = "http://${aws_eip.app.public_ip}:5173"
}

output "backend_url" {
  description = "Base URL for the backend API (use this as --backend-url for the Student Agent)"
  value       = "http://${aws_eip.app.public_ip}:8000"
}

output "ssh_command" {
  description = "SSH into the instance to check logs or troubleshoot"
  value       = "ssh -i <path-to-your-key.pem> ubuntu@${aws_eip.app.public_ip}"
}
