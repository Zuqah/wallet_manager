from web3 import Web3

def load_private_keys(file_path):
    wallets = []
    with open(file_path, 'r') as file:
        for line in file:
            address, private_key = line.strip().split(',')
            checksum_address = Web3.to_checksum_address(address)
            wallets.append({"address": checksum_address, "private_key": private_key})
    return wallets

infura_url = 'YOUR_RPC_URL_HERE'
web3 = Web3(Web3.HTTPProvider(infura_url))

if not web3.is_connected():
    raise ConnectionError("Failed to connect to the Ethereum network")

# MAKE TWO TEXT FILES
# ONE NAMED <wallets_consolidate.txt> AND ONE NAMED <main_wallet.txt>
# PUT YOUR ADDRESSES AND PRIVATE KEYS IN THIS FORMAT ON EACH LINE <ADDRESS,PRIVATEKEY>
# MAKE SURE THESE TWO TEXT FILES ARE IN THE SAME FOLDER AS THE MAIN PYTHON SCRIPT
# ONLY USE ONE LINE FOR <main.wallet.txt> SINCE IT IS ONLY ONE WALLET
# FORMAT IS ONE LINE PER WALLET
keys_file_path = 'wallets_consolidate.txt'
wallets = load_private_keys(keys_file_path)

main_file_path = 'main_wallet.txt'
main_wallet = load_private_keys(main_file_path)[0]

# Consolidation target wallet address
target_wallet = "YOUR_MAIN_WALLET_ADDRESS_HERE"

gas_price = (web3.eth.gas_price + 5000000000)
gwei_price = float(gas_price / 1000000000)
gas_limit = 21000
print(f'Gas in gwei: {gwei_price}')

def consolidate_eth(wallet, target_wallet):
    address = wallet['address']
    private_key = wallet['private_key']

    balance = web3.eth.get_balance(address)
    
    gas_fee = gas_price * gas_limit

    amount_to_send = balance - gas_fee

    if amount_to_send <= 0:
        print(f"Insufficient balance in wallet {address} for the transaction.")
        return

    nonce = web3.eth.get_transaction_count(address)
    tx = {
        'nonce': nonce,
        'to': target_wallet,
        'value': amount_to_send,
        'gas': gas_limit,
        'gasPrice': gas_price,
    }

    # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction complete for wallet {address}: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")

def disperse_eth(main_wallet, amount_to_disperse, num_wallets):
    main_wallet_address = main_wallet['address']
    main_wallet_private_key = main_wallet['private_key']

    # Convert ETH amount to Wei
    amount_to_disperse_wei = Web3.to_wei(amount_to_disperse, 'ether')
    
    for i, wallet in enumerate(wallets[:num_wallets]):
        address = wallet['address']
        
        nonce = web3.eth.get_transaction_count(main_wallet_address) + i  # Increment nonce for each transaction
        tx = {
            'nonce': nonce,
            'to': address,
            'value': amount_to_disperse_wei,
            'gas': gas_limit,
            'gasPrice': gas_price + (i * 1000000000),  # Increment gas price for each transaction
        }

        # Sign the transaction
        signed_tx = web3.eth.account.sign_transaction(tx, main_wallet_private_key)

        # Send the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Dispersed {amount_to_disperse} ETH to wallet {address}: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")

def send_message(main_wallet, message, addresses, num_messages):
    main_wallet_address = main_wallet['address']
    main_wallet_private_key = main_wallet['private_key']

    # Convert message to hex
    hex_message = Web3.to_hex(text=message)

    # Set a higher gas limit for transactions with data
    message_gas_limit = 30000  # Adjust as needed for larger messages

    valid_addresses = []
    for address in addresses:
        address = address.strip()  # Remove any extra spaces

        # Check if the address is an ENS name
        if address.endswith('.eth'):
            try:
                resolved_address = web3.ens.address(address)
                if resolved_address:
                    valid_addresses.append(Web3.to_checksum_address(resolved_address))
                else:
                    print(f"Unable to resolve ENS address: {address}")
            except Exception as e:
                print(f"Error resolving ENS address {address}: {e}")
        elif Web3.is_address(address):  # Validate the Ethereum address
            valid_addresses.append(Web3.to_checksum_address(address))
        else:
            print(f"Invalid address skipped: {address}")

    for i, address in enumerate(valid_addresses):
        for j in range(num_messages):
            nonce = web3.eth.get_transaction_count(main_wallet_address) + (i * num_messages) + j
            tx = {
                'nonce': nonce,
                'to': address,
                'value': 0,  # 0 ETH transaction
                'gas': message_gas_limit,  # Higher gas limit for data
                'gasPrice': gas_price + (j * 1000000000),  # Increment gas price slightly
                'data': hex_message,  # Message in hex format
            }

            # Sign the transaction
            signed_tx = web3.eth.account.sign_transaction(tx, main_wallet_private_key)

            # Send the transaction
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Message '{message}' sent to {address}: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")


def main():
    action = input("Enter 'consolidate' to consolidate ETH, 'disperse' to disperse ETH, or 'message' to send a message: ").strip().lower()
    
    if action == 'consolidate':
        for wallet in wallets:
            consolidate_eth(wallet, target_wallet)
    elif action == 'disperse':
        amount_to_disperse = float(input("Enter the amount of ETH to disperse to each wallet: ").strip())
        num_wallets = int(input(f"Enter the number of wallets to disperse ETH to (max {len(wallets)}): ").strip())
        
        if num_wallets > len(wallets):
            print(f"Error: You can only disperse ETH to up to {len(wallets)} wallets.")
        else:
            disperse_eth(main_wallet, amount_to_disperse, num_wallets)
    elif action == 'message':
        message = input("Enter the message you want to send: ").strip()
        addresses = input("Enter the recipient addresses separated by commas: ").strip().split(',')
        num_messages = int(input("Enter the number of times to send the message: ").strip())
        
        send_message(main_wallet, message, addresses, num_messages)
    else:
        print("Invalid action. Please enter 'consolidate', 'disperse', or 'message'.")

main()
