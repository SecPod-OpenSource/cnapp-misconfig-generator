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

resource "azurerm_resource_group" "fixture" {
  count    = var.allow_unsafe_apply ? 1 : 0
  name     = "cspm-azure-2024-0028-rg"
  location = var.azure_location
}

resource "azurerm_network_security_group" "fixture" {
  count               = var.allow_unsafe_apply ? 1 : 0
  name                = "cspm-azure-2024-0028-nsg"
  location            = azurerm_resource_group.fixture[0].location
  resource_group_name = azurerm_resource_group.fixture[0].name

  security_rule {
    name                       = "allow-public-ssh"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}
