from deployment.deployment import ISODeployment
import argparse
from deployment.logger import Logger
import sys


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    logger = Logger()
    parser.add_argument("-ph", '--pxe_host', type=str, default="", help='input pxe server host name or ip')
    parser.add_argument("-pu", '--pxe_user', type=str, default="root", help='input pxe ssh user name')
    parser.add_argument("-pp", '--pxe_password', type=str, default="nokia123", help='input pxe ssh password')
    parser.add_argument("-it", '--image_tag', type=str, default="0.38", help='input image tag of docker image')
    parser.add_argument("-fh", '--fhgw_host', type=str, default="", help='input fhgw host or ip')
    parser.add_argument("-fu", '--fhgw_user', type=str, default="_nokfhgwoperator", help='input fhgw ssh user name')
    parser.add_argument("-fp", '--fhgw_password', type=str, default="root", help='input fhgw ssh first password')
    parser.add_argument("-fr", '--fhgw_root_password', type=str, default="root", help='input fhgw ssh second password')
    parser.add_argument("-fv", '--fhgw_iso_version', type=str, default="", help='input fhgw expected iso version')
    parser.add_argument("-fg", '--fhgw_gateway', type=str, default="", help='input fhgw default gateway')
    parser.add_argument("-fm", '--fhgw_netmask', type=str, default="", help='input fhgw netmask')
    parser.add_argument("-bh", '--bmc_host', type=str, default="", help='input bmc host name or ip address')
    parser.add_argument("-bu", '--bmc_user', type=str, default="", help='input bmc ssh user name')
    parser.add_argument("-bp", '--bmc_password', type=str, default="", help='input bmc ssh password')
    parser.add_argument("-sn", '--sled_number', type=str, default="", help='input sled number')
    parser.add_argument("-pi", '--pxe_interface', type=str, default="", help='input pxe interface')
    args = parser.parse_args()
    pxe_host = args.pxe_host
    if not pxe_host:
        logger.error("pxe host is not set, please have a check !!!".title())
        sys.exit(-1)
    pxe_user = args.pxe_user
    pxe_password = args.pxe_password
    fhgw_host = args.fhgw_host
    if not fhgw_host:
        logger.error("fhgw host is not set, please have a check !!!".title())
        sys.exit(-1)
    fhgw_user = args.fhgw_user
    fhgw_password = args.fhgw_password
    fhgw_root_password = args.fhgw_root_password
    fhgw_iso_version = args.fhgw_iso_version
    bmc_host = args.bmc_host
    bmc_user = args.bmc_user
    bmc_password = args.bmc_password
    sled_number = args.sled_number
    pxe_interface = args.pxe_interface
    fhgw_gateway = args.fhgw_gateway
    fhgw_netmask = args.fhgw_netmask
    if not fhgw_iso_version:
        logger.error("fhgw expected iso version is not set, please have a check !!!".title())
        sys.exit(-1)
    image_tag = args.image_tag
    pxe_info = {"host": pxe_host,
                "username": pxe_user,
                "password": pxe_password
                }
    fhgw_info = {"host": fhgw_host,
                 "username": fhgw_user,
                 "password": fhgw_password,
                 "root_password": fhgw_root_password
                 }
    bmc_info = {"host": bmc_host,
                "username": bmc_user,
                "password": bmc_password
                }

    iso_deployment = ISODeployment(pxe_info=pxe_info,
                                   fhgw_info=fhgw_info,
                                   bmc_info=bmc_info,
                                   logger=logger,
                                   fhgw_iso_version=fhgw_iso_version,
                                   sled_number=sled_number,
                                   pxe_interface=pxe_interface,
                                   fhgw_netmask=fhgw_netmask,
                                   fhgw_gateway=fhgw_gateway,
                                   image_tag=image_tag)
    iso_deployment.execute()
