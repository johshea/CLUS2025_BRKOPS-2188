shared_module = '''
resource "meraki_networks" "this" {
  name            = local.network.network.name
  product_types   = local.network.network.productTypes
  time_zone        = local.network.network.timeZone
  tags            = local.network.network.tags
  organization_id = local.network.network.organizationId
}

resource "meraki_networks_wireless_ssids" "all_ssids" {
  for_each = local.ssid

  network_id                      = local.network.network.id
  number                          = each.value.number
  name                            = each.value.name
  auth_mode                       = each.value.authMode
  encryption_mode                 = contains(keys(each.value), "encryptionMode") ? each.value.encryptionMode : null
  wpa_encryption_mode             = contains(keys(each.value), "wpaEncryptionMode") ? each.value.wpaEncryptionMode : null
  psk                             = contains(keys(each.value), "wpaPreSharedKey") ? each.value.wpaPreSharedKey : null
  ip_assignment_mode              = each.value.ipAssignmentMode
  default_vlan_id                 = contains(keys(each.value), "defaultVlanId") ? each.value.defaultVlanId : null
  adult_content_filtering_enabled = contains(keys(each.value), "adultContentFilteringEnabled") ? each.value.adultContentFilteringEnabled : null
  use_vlan_tagging                = contains(keys(each.value), "useVlanTagging") ? each.value.useVlanTagging : null
  enabled                         = each.value.enabled
  lan_isolation_enabled           = contains(keys(each.value), "lanIsolationEnabled") ? each.value.lanIsolationEnabled : null
}  

  //  enable MX vlans
resource "meraki_networks_appliance_vlans_settings" "vlan_settings" {
  network_id = local.network.network.id
  vlans_enabled = true
}

  # insert a timout to allow vlans = true to be recognized by the backend
resource "time_sleep" "wait_20_seconds" {
  depends_on = [meraki_networks_appliance_vlans_settings.vlan_settings]
  create_duration = "30s"
}

 resource "meraki_networks_appliance_vlans" "vlan" {
  for_each = local.mxvlan

  network_id   = local.network.network.id
  id           = each.value.vlan_id
  name         = contains(keys(each.value), "name") ? each.value.name : null
  subnet       = contains(keys(each.value), "subnet") ? each.value.subnet : null
  appliance_ip = contains(keys(each.value), "appliance_ip") ? each.value.appliance_ip : null

  depends_on = [time_sleep.wait_20_seconds]
}

'''

tf_provider = '''terraform {
                      required_providers {
                        meraki = {
                          source  = "cisco-open/meraki"
                           version = "1.1.2-beta"
                        }
                      }
                    }
                    
                    provider "meraki" {
                      meraki_dashboard_api_key  = var.api_key
                    }
                    '''

tf_variables = '''variable "api_key" {
                          type        = string
                          description = "API key for Meraki provider"
                          sensitive = true
                        }
            
                        variable "org_id" {
                          type        = string
                          description = "org id for the dashboard org"
                          sensitive = true
                        }
            '''