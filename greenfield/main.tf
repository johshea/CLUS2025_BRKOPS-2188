

#module "org" {
  #source = "./modules/organization"
  #org_id = var.org_id
#}

module "networks" {
  source = "./modules/networks"
  api_key = var.api_key
  org_id = var.org_id
  network_name = var.network_name
}

module "ssid" {
  source = "./modules/ssid"
  api_key = var.api_key
  org_id = var.org_id
  network_name = var.network_name
  network_id = module.networks.network_id
}

module "mx_vlans" {
  source = "./modules/mx_vlans"
  api_key = var.api_key
  network_name = var.network_name
  network_id = module.networks.network_id
}

