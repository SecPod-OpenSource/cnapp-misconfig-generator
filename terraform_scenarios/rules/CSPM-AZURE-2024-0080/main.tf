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
  name     = "cspm-azure-2024-0080-rg"
  location = var.azure_location
}

resource "azurerm_managed_disk" "fixture" {
  count                = var.allow_unsafe_apply ? 1 : 0
  name                 = "cspm-azure-2024-0080-disk"
  location             = azurerm_resource_group.fixture[0].location
  resource_group_name  = azurerm_resource_group.fixture[0].name
  storage_account_type = "Standard_LRS"
  create_option        = "Empty"
  disk_size_gb         = 4
}
