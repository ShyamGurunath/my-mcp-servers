import psutil
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Path


mcp = FastMCP("System info")

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    ram = psutil.virtual_memory()
    return ram.percent

def get_ram_usage_in_gb():
    ram = psutil.virtual_memory()
    return round(ram.used / 1e9, 2)

def get_disk_usage():
    disk = psutil.disk_usage("/")
    return disk.percent


@mcp.resource("info://cpu")
def cpu_usage():
    """Get the CPU usage of the system."""
    return get_cpu_usage()

@mcp.resource("info://ram")
def ram_usage():
    """Get the RAM usage of the system."""
    return get_ram_usage()

@mcp.tool()
def total_usage_ram_in_gb():
    """Get the total RAM usage of the system in GB."""
    return get_ram_usage_in_gb()

@mcp.tool()
def disk_usage():
    """Get the disk usage of the system."""
    return get_disk_usage()

@mcp.prompt()
def generate_prompt():
    """Generate a prompt for the user."""
    return "What is the current CPU usage & disk usage & ram usage ?"


if __name__=="__main__":
    mcp.run(transport="stdio")
