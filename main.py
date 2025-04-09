from enum import Enum
from getpass import getpass
from impacket.smbconnection import SMBConnection
from impacket.dcerpc.v5 import wkst, srvs

# Define intensity levels using an Enum for type safety and clarity
class IntensityLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

# Class to handle SMB connection and enumeration logic
class SMBEnumerator:
    def __init__(self, target, username, password, domain):
        """Initialize the SMBEnumerator with target and credentials."""
        self.target = target
        self.username = username
        self.password = password
        self.domain = domain
        self.conn = None

    def connect(self):
        """Establish an SMB connection to the target."""
        try:
            self.conn = SMBConnection(self.target, self.target)
            self.conn.login(self.username, self.password, self.domain)
        except Exception as e:
            print(f"Error establishing SMB connection: {e}")
            raise

    def disconnect(self):
        """Close the SMB connection if it exists."""
        if self.conn:
            self.conn.close()

    def enumerate_low(self):
        """Perform basic enumeration (list shares)."""
        print("Performing basic enumeration...")
        shares = self.conn.listShares()
        print("\n[+] Shares found:")
        for share in shares:
            print(f"  - {share['shi1_netname']}")

    def enumerate_medium(self):
        """Perform medium enumeration (list logged-on users)."""
        print("Performing medium enumeration...")
        dce = self.conn.getDCE()
        dce.connect()
        dce.bind(wkst.MSRPC_UUID_WKST)
        request = wkst.NetrWkstaUserEnum()
        response = dce.request(request)
        print("\n[+] Logged-on users found:")
        for user in response['UserInfo']['WkstaUserInfo']:
            print(f"  - {user['wkui1_username']}")

    def enumerate_high(self):
        """Perform advanced enumeration (sessions, writable shares, services)."""
        print("Performing advanced enumeration...")

        # Enumerate active sessions
        print("\n[+] Enumerating active sessions...")
        try:
            dce = self.conn.getDCE()
            dce.connect()
            dce.bind(srvs.MSRPC_UUID_SRVS)
            request = srvs.NetrSessionEnum()
            response = dce.request(request)
            if response['SessionInfo']['Level'] == 10:
                sessions = response['SessionInfo']['SessionInfo10']
                for session in sessions:
                    print(f"  - User: {session['sesi10_username']}, "
                          f"Client: {session['sesi10_cname']}, "
                          f"Active Time: {session['sesi10_time']}")
            else:
                print("No active sessions found.")
        except Exception as e:
            print(f"Error enumerating sessions: {e}")

        # Check writable shares
        print("\n[+] Checking writable/exploitable shares...")
        try:
            shares = self.conn.listShares()
            for share in shares:
                share_name = share['shi1_netname']
                if not share_name.endswith('$'):
                    try:
                        self.conn.listPath(share_name, '*')
                        print(f"  - Share '{share_name}' is accessible.")
                    except Exception as e:
                        print(f"  - Share '{share_name}' is not accessible: {e}")
        except Exception as e:
            print(f"Error checking writable shares: {e}")

        # Enumerate services (requires additional privileges)
        print("\n[+] Enumerating services (requires additional privileges)...")
        try:
            dce.bind(srvs.MSRPC_UUID_SRVS)
            request = srvs.NetrServerGetInfo()
            response = dce.request(request)
            server_info = response['ServerInfo']['ServerName']
            print(f"Server Name: {server_info}")
        except Exception as e:
            print(f"Error enumerating services: {e}")

    def enumerate(self, intensity):
        """Perform enumeration based on the specified intensity level."""
        self.connect()
        try:
            if intensity == IntensityLevel.LOW:
                self.enumerate_low()
            elif intensity == IntensityLevel.MEDIUM:
                self.enumerate_medium()
            elif intensity == IntensityLevel.HIGH:
                self.enumerate_high()
            else:
                print("Invalid intensity level selected.")
        finally:
            self.disconnect()

# Class to handle user input
class UserInputHandler:
    @staticmethod
    def get_target():
        """Prompt for and return the target IP or hostname."""
        return input("Enter target IP or hostname: ")

    @staticmethod
    def get_username():
        """Prompt for and return the username."""
        return input("Enter username: ")

    @staticmethod
    def get_password():
        """Prompt for and return the password securely."""
        return getpass("Enter password: ")

    @staticmethod
    def get_domain():
        """Prompt for and return the domain name."""
        return input("Enter domain name (e.g., WORKGROUP): ")

    @staticmethod
    def get_intensity_level():
        """Prompt for and return the selected intensity level."""
        print("Select intensity level:")
        for level in IntensityLevel:
            print(f"{level.value}. {level.name}")
        while True:
            try:
                selected_level = int(input("Enter your choice: "))
                return IntensityLevel(selected_level)
            except ValueError:
                print("Invalid selection. Please choose a valid intensity level.")

# Main execution block
if __name__ == "__main__":
    try:
        # Get user input
        target = UserInputHandler.get_target()
        username = UserInputHandler.get_username()
        password = UserInputHandler.get_password()
        domain = UserInputHandler.get_domain()
        intensity = UserInputHandler.get_intensity_level()

        # Create enumerator instance and perform enumeration
        enumerator = SMBEnumerator(target, username, password, domain)
        enumerator.enumerate(intensity)
    except Exception as e:
        print(f"An error occurred: {e}")
