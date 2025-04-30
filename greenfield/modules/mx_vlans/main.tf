locals {
  appliance = yamldecode(file("./network_${var.network_name}/appliance_settings.yaml"))

  //flatten vlan data
  vlans    = local.appliance["vlans"]
  mx_vlans = flatten([for vlan in local.vlans :
    {
      "vlan_id"         = vlan.vlan_id
      "name"            = vlan.name
      "dns_nameservers" = vlan.dns
      "subnet"          = vlan.subnet
      "appliance_ip"    = vlan.appliance_ip
      #dhcp_handling = vlan.dhcp_handling
      #dns_nameservers = vlan.dns_nameservers
    }
  ])
}

//  enable MX vlans
resource "meraki_networks_appliance_vlans_settings" "vlan_settings" {
  network_id = var.network_id
  vlans_enabled = true
}

# insert a timout to allow vlans = true to be recognized by the backend
resource "time_sleep" "wait_20_seconds" {
  depends_on = [meraki_networks_appliance_vlans_settings.vlan_settings]
  create_duration = "30s"
}

resource "meraki_networks_appliance_vlans" "vlan" {
   for_each = {
    for vlan in local.mx_vlans : vlan.vlan_id => vlan}

  network_id   = var.network_id
  id           = each.value.vlan_id
  name         = each.value.name
  subnet       = each.value.subnet
  appliance_ip = each.value.appliance_ip

  depends_on = [time_sleep.wait_20_seconds]
}
