terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}

variable "azure_subscription_id" {
  description = "Azure subscription ID for the dedicated test subscription."
  type        = string
}

variable "azure_location" {
  description = "Azure region for the fixture."
  type        = string
  default     = "centralindia"
}

variable "allow_unsafe_apply" {
  description = "Must be explicitly true before this intentionally insecure fixture is created."
  type        = bool
  default     = false
}

variable "sql_admin_password" {
  description = "Password for the disposable Azure SQL administrator. Set TF_VAR_sql_admin_password."
  type        = string
  sensitive   = true
}

resource "random_string" "fixture" {
  length  = 10
  special = false
  upper   = false
}

resource "azurerm_resource_group" "fixture" {
  count    = var.allow_unsafe_apply ? 1 : 0
  name     = "cspmazure20240050-rg"
  location = var.azure_location
}

resource "azurerm_mssql_server" "fixture" {
  count                         = var.allow_unsafe_apply ? 1 : 0
  name                          = "cspm${random_string.fixture.result}"
  resource_group_name           = azurerm_resource_group.fixture[0].name
  location                      = azurerm_resource_group.fixture[0].location
  version                       = "12.0"
  administrator_login           = "fixtureadmin"
  administrator_login_password  = var.sql_admin_password
  public_network_access_enabled = true

}

resource "azurerm_mssql_database" "fixture" {
  count     = var.allow_unsafe_apply ? 1 : 0
  name      = "fixturedb"
  server_id = azurerm_mssql_server.fixture[0].id
  sku_name  = "Basic"
}

resource "azurerm_mssql_firewall_rule" "any" {
  count            = var.allow_unsafe_apply ? 1 : 0
  name             = "AllowAllIPv4"
  server_id        = azurerm_mssql_server.fixture[0].id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}
