#!/bin/bash
#
# Copyright @ Nokia 2019. All rights reserved.
IP_ADDRESS=""
boot_priority_json="./boot_priority.json"
tmp_boot_priority_json="/tmp/boot_priority.json"
tmp_redfish_log="/tmp/redfish.log"

change_boot_device_priority()
{
    _local=""
    rm -f $tmp_redfish_log
    curl -s -k -u "$USERNAME:$PASSWORD" -H "Content-Type: application/json" \
    -H If-None-Match:"W/\"1\"" -X PATCH -d @$tmp_boot_priority_json \
    https://$IP_ADDRESS/redfish/v1/Systems/Self > $tmp_redfish_log
    [ $? -ne 0 ] && _error="set"
    if [ -s "$tmp_redfish_log" ]; then
        grep -i "error" $tmp_redfish_log >/dev/null
        [ $? -eq 0 ] && _error="set"
    fi
    if [ -n "$_error" ];then
	    echo -e "Failed to set the boot priority to $BOOTDEVICE and mode $BOOT_MODE."
	    echo -e "Please retry the command after some time"
	    [ -f $tmp_redfish_log ] && echo -e "\nBelow is the response from BMC\n" \
		    && cat $tmp_redfish_log && echo -e "\n" && rm -f $tmp_redfish_log
	    exit 8
    fi
    echo "Configured the BIOS with ${BOOTDEVICE} as the boot device and ${BOOT_MODE} as mode with source override as ${SOURCE_OVERRIDE}"

}

restart_server()
{
    local _error=""
    rm -f $tmp_redfish_log
    echo "Restarting the Server"
    curl -s -k -u "$USERNAME:$PASSWORD" -H "Content-Type: application/json" -X POST \
    https://$IP_ADDRESS/redfish/v1/Chassis/Self/Actions/Chassis.Reset -d '{"ResetType":"ForceRestart"}' > $tmp_redfish_log
    [ $? -ne 0 ] && _error="set"
    if [ -s "$tmp_redfish_log" ]; then
        grep -i "error" $tmp_redfish_log >/dev/null
        [ $? -eq 0 ] && _error="set"
    fi
    if [ -n "$_error" ];then
        echo -e "Failed to restart the server. Please retry the command after some time"
	[ -f $tmp_redfish_log ] && echo -e "\nBelow is the response from BMC\n" \
	       	&& cat $tmp_redfish_log && echo -e "\n" && rm -f $tmp_redfish_log
	exit 9
    fi
    echo "Restarted the server successfully"
}

generate_boot_priority_json()
{
    [ ! -f $boot_priority_json ] && echo "Unable to locate $boot_priority_json" && exit 7
    cp $boot_priority_json $tmp_boot_priority_json
    sed -i "s/SOURCE_OVERRIDE/$SOURCE_OVERRIDE/;s/BOOTDEVICE/$BOOTDEVICE/;s/BOOT_MODE/$BOOT_MODE/" $tmp_boot_priority_json
}

validate_ip()
{
    local IP=$1
    if [[ $IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        ping -c 1 -W 1 $IP >/dev/null 2>&1
        [ $? -eq 0 ] && echo "IP is valid"
    fi
}

usage()
{
    echo "$0 -i <BMC ip address> -u <username> -p <paswd> -m <bootmode> -b <bootdevice> -o <source override> [ -w ]"
    echo "-b <Pxe|Cd|Usb|Hdd|Floppy> BootSourceOverrideTarget"
    echo "-o <Once|Continuous>"
    echo "-u <Username>"
    echo "-m <Legacy|UEFI>"
    echo "-p <Redfish Password>"
    echo "-w WITHOUT RESET"
}

while getopts ":i:b:o:u:p:m:wh:" opt; do
  case $opt in
    i) IP_ADDRESS="$OPTARG"
    ;;
    b) BOOTDEVICE="$OPTARG"
    ;;
    p) PASSWORD="$OPTARG"
    ;;
    u) USERNAME="$OPTARG"
    ;;
    o) SOURCE_OVERRIDE="$OPTARG"
    ;;
    m) BOOT_MODE="$OPTARG"
    ;;
    w) WITHOUT_RESET="yes"
    ;;
    h) usage && exit 1
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

if [ -z "$IP_ADDRESS" -o -z "$BOOTDEVICE" -o -z "$SOURCE_OVERRIDE" -o -z "$BOOT_MODE" -o -z "$PASSWORD" -o -z "$USERNAME" ];then
    usage && exit 2
fi

if [[ "${BOOTDEVICE}" != +(Pxe|Cd|Usb|Hdd|Floppy) ]]; then
    usage && exit 3
fi

if [[ "${SOURCE_OVERRIDE}" != +(Once|Continuous) ]]; then
    usage && exit 4
fi

if [[ "${BOOT_MODE}" != +(Legacy|UEFI) ]]; then
    usage && exit 5
fi

status=$(validate_ip $IP_ADDRESS)

[ -z "$status" ] && echo "BMC IP address is Invalid or not reachable. Please check and try again" && exit 6

generate_boot_priority_json
change_boot_device_priority
[ -z $WITHOUT_RESET ] && restart_server
rm -f $tmp_boot_priority_json $tmp_redfish_log
exit 0
