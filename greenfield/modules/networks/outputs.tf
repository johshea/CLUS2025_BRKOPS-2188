output "network_id" {
  description = "The ID of the created Meraki network"
  value       = meraki_networks.network.id
}