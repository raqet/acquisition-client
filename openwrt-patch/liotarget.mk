#
# Copyright (C) 2006-2009 OpenWrt.org
#
# This is free software, licensed under the GNU General Public License v2.
# See /LICENSE for more information.
#

BLOCK_MENU:=Block Devices

define KernelPackage/liotarget
  SUBMENU:=$(BLOCK_MENU)
  TITLE:=Linux IO Target
  DEPENDS:=@TARGET_x86
  KCONFIG:=CONFIG_TARGET_CORE \
	  CONFIG_TCM_IBLOCK \
	  CONFIG_TCM_FILEIO \
	  CONFIG_ISCSI_TARGET
  FILES=$(LINUX_DIR)/drivers/target/target_core_mod.ko \
	$(LINUX_DIR)/drivers/target/iscsi/iscsi_target_mod.ko \
	$(LINUX_DIR)/drivers/target/target_core_iblock.ko \
	$(LINUX_DIR)/drivers/target/target_core_file.ko
  AUTOLOAD:=$(call AutoLoad,30, target_core_mod iscsi_target_mod target_core_iblock target_core_file,1)
endef

define KernelPackage/liotarget/description
  Kernel module for Linux IO Target
endef

$(eval $(call KernelPackage,liotarget))



