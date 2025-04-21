# import tabulate  # bruh no wifi on the plane
import sys
import yaml
from typing import TypedDict, NewType, Literal

import networkx as nx
import matplotlib.pyplot as plt

# TODO
TODOS = [
    "multiple __edgeservices",  # dc and the like should connect to the other hosts
    "list of lists",
    "ini inventory",
]

# constants
ALL = "all"
UNIX = "nix"
DOS = "windows"
HOSTS = "hosts"
OS = "os"
IP = "ansible_host"
SERVICES = "services"
DC = "domaincontroller"
RDP = "rdp"
VARS = "vars"
__edgeservices = [DC, ]  # I want all caps to be keywords in Ansible

# type annotations
HostName = NewType("HostName", str)  # lightweight #define that's basically a comment
class HostMetadata(TypedDict):
    os: str
    ansible_host: str
    services: list[str]
    index: int
    diagram_label: str
HostEntries = dict[HostName, HostMetadata]


# callbacks for labeling the graph
hosts_to_indices = {}
def index_labeler(label:str) -> str:
    '''swap out label with a number (to fit in the nx node)'''
    global hosts_to_indices
    try:
        return str(hosts_to_indices[label])
    except KeyError as e:
        print(f"Host \"{label}\" not assigned an index, likely a bug on my end not yours\ntry either full name or custom labeling\nhosts_to_indices: {hosts_to_indices}")
        raise e
def custom_labeler(label:str) -> str:
    '''
    will change what is portrayed on the nx graph\\
    this is designed to be overwritten with a custom implementation
    '''
    return label
def full_labeler(label:str) -> str:
    '''seems unnecessary but lets me do mickey mouse things with func ptrs'''
    return label
labeler_callback = full_labeler  # this is a pointer to the function, so we can change it later


def gen_host_metadata(os_name: str = "", ip_addr: str = "", services: list[str] = None) -> HostMetadata:
    if services is None:
        # no we cannot pass a default value of [] because it persists across calls
        services = []
    return HostMetadata(
        os=os_name,
        ansible_host=ip_addr,
        services=services,
    )


def tablify(hosts: HostEntries, network_diagram: str, border: int|float = 2, width: int|float = 50) -> str:
    '''hosts should map {host_name: metadata_dict}'''

    # me when python is a scripting language
    assert isinstance(border, (int, float))  # can you even have floats?? pov django class failed you
    assert isinstance(width, (int, float))
    
    is_dict = isinstance(hosts, dict)
    is_list = isinstance(hosts, list)
    if "list of lists" in TODOS:
        assert is_dict
    else:
        if is_list:
            # list of lists gogogo
            assert isinstance((hosts+[[]])[0], list)  # based everythong is first class object
        else:
            assert is_dict
    
    tab_inc = 0
    tabs = lambda: "\t"*tab_inc  # hacky way to indent the html

    html = tabs() + "<head>\n"
    tab_inc += 1
    
    html += tabs() + '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    html += tabs() + "<h1>Network Diagram from Inventory</h1>\n"  # title
    html += tabs() + "<link rel='stylesheet' href='./styles.css'>\n"
    
    tab_inc -= 1
    html += tabs() + "</head>\n"

    # Adding the network diagram image
    html += '<div style="text-align: center;">\n'
    tab_inc += 1
    html += tabs() + f'<img src="{network_diagram}" alt="Network Diagram" style="max-width: 100%; height: auto;">\n'
    tab_inc -= 1
    html += '</div>\n'

    html += f"<table style='position: relative; width: 800px; height: 600px;' border={border}>\n"
    tab_inc += 1
    html += tabs() + "<tbody>\n"
    tab_inc += 1
    html += tabs() + f"<td>Index</td> <td>Host Name</td> <td>Host Address</td> <td>OS</td> <td>Services</td> <td>Diagram Label</td>\n"

    for host in hosts:
        index = hosts_to_indices[host]
        system = hosts[host][OS]
        addr = hosts[host][IP]
        services = hosts[host][SERVICES]
        diagram_label = hosts[host]["diagram_label"]  # ok so by convention, I want constants to be keywords in Ansible and thus I am hardcoding the string here

        html += tabs() + "<tr>\n"
        tab_inc += 1
        html += tabs() + f"<td>{index}</td> <td>{host}</td> <td>{addr}</td> <td>{system}</td> <td>"
        
        for service in services[:-1]:
            html += f"{service}, "
        if len(services) >= 1:
            html += f"{services[-1]}"

        html += f"</td> <td>{diagram_label}</td>\n"

        tab_inc -= 1
        html += "</td>\n" + tabs() + "</tr>\n"

    tab_inc -= 1
    html += tabs() + "</tbody>\n</table>"
    tab_inc -= 1

    return html


def load_inventory(file: str) -> dict:
    inventory = None
    with open(file, "r") as f:
        inventory = yaml.safe_load(f)
    if inventory is None:
        print(f"couldn't load {file} as yaml")
        raise IOError
    return inventory


def parse_ansible(inventory: dict, out_file: str = "net") -> tuple[HostEntries, nx.Graph]:
    global hosts_to_indices
    global labeler_callback

    hosts: HostEntries = {}
    edge_hosts = []
    netgram = nx.Graph()
    counter = 0

    for system, config in inventory.items():
        if HOSTS not in config:
            continue
        elif system == ALL:
            continue  # uh does ansible let you specify services in this?

        elif system in [UNIX, DOS]:
            for host in config[HOSTS]:
                if host not in hosts:
                    hosts_to_indices[host] = counter
                    counter += 1
                    actual_os = ("unspecified " + system) if OS not in config[HOSTS][host] else config[HOSTS][host][OS]  # see this is whats called mickey mousery over readability W
                    ip_addr = "" if IP not in config[HOSTS][host] else config[HOSTS][host][IP]
                    hosts[host] = gen_host_metadata(actual_os, ip_addr)
                    hosts[host]["diagram_label"] = labeler_callback(host)
                    netgram.add_node(hosts[host]["diagram_label"])
                else:
                    print(f"host \'{host}\' already exists, skipping subsequent entries")
        else:
            for host in config[HOSTS]:
                if system in __edgeservices:
                    edge_hosts.append(labeler_callback(host))

                if host in hosts:
                    hosts[host][SERVICES].append(system)
                else:
                    actual_os = "" if OS not in config[HOSTS][host] else config[HOSTS][host][OS]
                    ip_addr = "" if IP not in config[HOSTS][host] else config[HOSTS][host][IP]
                    hosts[host] = gen_host_metadata(actual_os, ip_addr)
                    hosts_to_indices[host] = counter
                    netgram.add_node(labeler_callback(host))
                    counter += 1

    for edge in edge_hosts:
        for node in netgram.nodes:
            if edge != node:
                netgram.add_edge(edge, node)

    nx.draw(netgram, with_labels=True)
    plt.savefig(f"{out_file}.png")

    return hosts


def main(file: str, out_file: str = "net", graph_labeling: Literal["custom", "indices", "full name"]= "full name") -> None:
    '''
        takes the name of the yaml file and generates .html and .pdf\\
        if output file name is not provided, it defaults to net.html(.pdf)\\
        graph labeling can be full name, indices, or custom (you must override the custom_labeler() function yourself)
    '''

    # uhhh this seems really finnicky, however, copus maximus
    global labeler_callback
    if graph_labeling == "custom":
        labeler_callback = custom_labeler
    elif graph_labeling == "full name":
        labeler_callback = full_labeler
    elif graph_labeling == "indices":
        labeler_callback = index_labeler
    else:
        raise ValueError("graph_labeling must be one of full name, indices, or custom")
    
    # reset global var
    global hosts_to_indices
    hosts_to_indices = {}

    # get fields from ansible inventory
    inventory = load_inventory(file)
    hosts = parse_ansible(inventory, out_file)

    # generate html
    html = tablify(hosts, f"{out_file}.png")
    with open(f"{out_file}.html", "w") as f:
        f.write(html)

    # generate pdf from that html
    msg = f"html and pdf saved to {out_file}.html and {out_file}.pdf"
    try:
        import pdfkit
        options = { "enable-local-file-access": "" }  # https://stackoverflow.com/questions/62814607/pdfkit-warning-blocked-access-to-file
        pdfkit.from_file(f"{out_file}.html", f"{out_file}.pdf", options=options)
    except ImportError as e:
        print("pdfkit not installed, html will still be produced but not the pdf")
        msg = str(e)
    except OSError as e:
        print("wkhtmltopdf not found and is a dependency of pdfkit, html will still be produced but not the pdf")
        msg = str(e)
    finally:
        print(msg)


if __name__ == "__main__":
    argc = len(sys.argv)
    assert argc <= 4
    
    file = "example.yaml" if argc < 2 else sys.argv[1]
    out_file = "net" if argc < 3 else sys.argv[2]
    labeler = "full name" if argc < 4 else sys.argv[3]

    main(file, out_file, labeler)
