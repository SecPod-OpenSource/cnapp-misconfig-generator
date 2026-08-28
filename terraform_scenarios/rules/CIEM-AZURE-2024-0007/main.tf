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

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "fixture" {
  count    = var.allow_unsafe_apply ? 1 : 0
  name     = "ciem-azure-2024-0007-rg"
  location = var.azure_location
}

resource "azurerm_role_definition" "fixture" {
  count       = var.allow_unsafe_apply ? 1 : 0
  name        = "ciem-azure-2024-0007-excessive"
  scope       = azurerm_resource_group.fixture[0].id
  description = "INTENTIONALLY INSECURE: grants all Azure actions"

  permissions {
    actions = ["*"]
  }

  assignable_scopes = [azurerm_resource_group.fixture[0].id]
}

resource "azurerm_role_assignment" "fixture" {
  count              = var.allow_unsafe_apply ? 1 : 0
  scope              = azurerm_resource_group.fixture[0].id
  role_definition_id = azurerm_role_definition.fixture[0].role_definition_resource_id
  principal_id       = data.azurerm_client_config.current.object_id
}
