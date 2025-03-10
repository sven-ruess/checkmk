#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# Example output from agent:
# <<<emcvnx_hwstatus>>>
# DPE7 Bus 0 Enclosure 0
# Enclosure Drive Type: SAS
# Current Speed: 6Gbps
# Maximum Speed: 6Gbps
# SP A State:                 Present
# SP B State:                 Present
# Bus 0 Enclosure 0 Power A State: Present
# Bus 0 Enclosure 0 Power B State: Present
# Bus 0 Enclosure 0 SPS A State: Present
# Bus 0 Enclosure 0 SPS B State: Present
# Bus 0 Enclosure 0 SPS A Cabling State: Valid
# Bus 0 Enclosure 0 SPS B Cabling State: Valid
# Bus 0 Enclosure 0 CPU Module A State: Present
# Bus 0 Enclosure 0 CPU Module B State: Present
# Bus 0 Enclosure 0 SP A I/O Module 0 State: Present
# Bus 0 Enclosure 0 SP A I/O Module 1 State: Empty
# Bus 0 Enclosure 0 SP B I/O Module 0 State: Present
# Bus 0 Enclosure 0 SP B I/O Module 1 State: Empty
# Bus 0 Enclosure 0 DIMM Module A State: Present
# Bus 0 Enclosure 0 DIMM Module B State: Present
#
# DAE6S Bus 0 Enclosure 1
# Enclosure Drive Type: SAS, NL SAS
# Current Speed: 6Gbps
# Maximum Speed: 6Gbps
# Bus 0 Enclosure 1 Power A State: Present
# Bus 0 Enclosure 1 Power B State: Present
# Bus 0 Enclosure 1 LCC A State: Present
# Bus 0 Enclosure 1 LCC B State: Present
# Bus 0 Enclosure 1 LCC A Revision: 1.33
# Bus 0 Enclosure 1 LCC B Revision: 1.33
# Bus 0 Enclosure 1 LCC A Serial #: US1V2120601546
# Bus 0 Enclosure 1 LCC B Serial #: US1V2120602428
# Bus 0 Enclosure 1 LCC A Current Speed: 6Gbps
# Bus 0 Enclosure 1 LCC B Current Speed: 6Gbps
# Bus 0 Enclosure 1 LCC A Maximum Speed: 6Gbps
# Bus 0 Enclosure 1 LCC B Maximum Speed: 6Gbps
#
# DAE6S Bus 1 Enclosure 0
# Enclosure Drive Type: SAS, NL SAS
# Current Speed: 6Gbps
# Maximum Speed: 6Gbps
# Bus 1 Enclosure 0 Power A State: Present

# Parse agent output into a dict of the form:
# parsed = {
#     "0/1" : {
#         "Power A" : "Present",
#         "Power B" : "Present",
#         # ...
#     }
# }


# mypy: disable-error-code="var-annotated"

from cmk.agent_based.legacy.v0_unstable import LegacyCheckDefinition

check_info = {}


def parse_emcvnx_hwstatus(info):
    parsed = {}
    for line in info:
        # recognice Enclosures by a line like
        # DAE6S Bus 0 Enclosure 1
        # with maybe an additional error message if Overall Status is not ok
        if len(line) > 3 and line[1] == "Bus" and line[3] == "Enclosure":
            encid = line[2] + "/" + line[4]
            enc = {}
            parsed[encid] = enc
            if len(line) > 5:
                enc["Overall Status"] = line[5].replace("*", "")
            else:
                enc["Overall Status"] = "No Errors Reported"
        # recognice Enclosures by a line like
        # SPE5 Enclosure SPE
        # with maybe an additional error message if Overall Status is not ok
        elif len(line) > 2 and line[1] == "Enclosure":
            encid = line[2]
            enc = {}
            parsed[encid] = enc
            if len(line) > 3:
                enc["Overall Status"] = line[3].replace("*", "")
            else:
                enc["Overall Status"] = "No Errors Reported"
        # gather additional information about an Enclosure found in one
        # of the cases above
        elif len(line) > 2 and line[-2] == "State:":
            if line[0] == "SP":
                device = line[0] + " " + line[1]
            else:
                device = " ".join(line[4:-2])
            state = line[-1]
            enc[device] = state
    return parsed


def inventory_emcvnx_hwstatus(section):
    inventory = []
    for enclosure in section:
        for device in section[enclosure]:
            if section[enclosure][device] != "Empty":
                inventory.append((enclosure + " " + device, None))
    return inventory


def check_emcvnx_hwstatus(item, _no_params, section):
    enc, device = item.split(" ", 1)
    try:
        devstate = section[enc][device]
        if devstate in ("Present", "Valid", "No Errors Reported"):
            nagstate = 0
        else:
            nagstate = 2
        return nagstate, f"Enclosure {item} is {devstate}"

    except KeyError:
        return 3, "Enclosure %s not found in agent output" % item


check_info["emcvnx_hwstatus"] = LegacyCheckDefinition(
    name="emcvnx_hwstatus",
    service_name="Enclosure %s",  # Example for Item: "0/1 Power A",
    parse_function=parse_emcvnx_hwstatus,
    discovery_function=inventory_emcvnx_hwstatus,
    check_function=check_emcvnx_hwstatus,
)
