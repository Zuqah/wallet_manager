from web3 import Web3
import json

def load_wallets(file_path):
    wallets = []
    with open(file_path, 'r') as file:
        for line in file:
            address, private_key = line.strip().split(',')
            checksum_address = Web3.to_checksum_address(address)
            wallets.append({"address": checksum_address, "private_key": private_key})
    return wallets

quicknode_url = 'ENTER YOUR NODE URL HERE'
web3 = Web3(Web3.HTTPProvider(quicknode_url))

if not web3.is_connected():
    raise ConnectionError("Failed to connect to the Ethereum network")

wallets_file_path = 'wallets.txt'
wallets = load_wallets(wallets_file_path)

main_file_path = 'main_wallet.txt'
main_wallet = load_wallets(main_file_path)[0]

target_wallet = "ENTER YOUR MAIN WALLET ADDRESS HERE"

gas_price = web3.eth.gas_price + 5000000000 # adds 5 gwei to the current gwei
gas_limit = 21000

disperse_abi = json.loads("""
[{"constant":false,"inputs":[{"name":"token","type":"address"},{"name":"recipients","type":"address[]"},{"name":"values","type":"uint256[]"}],"name":"disperseTokenSimple","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"token","type":"address"},{"name":"recipients","type":"address[]"},{"name":"values","type":"uint256[]"}],"name":"disperseToken","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"recipients","type":"address[]"},{"name":"values","type":"uint256[]"}],"name":"disperseEther","outputs":[],"payable":true,"stateMutability":"payable","type":"function"}]
""")
disperse_contract_address = "0xD152f549545093347A162Dce210e7293f1452150"
disperse_contract = web3.eth.contract(address=Web3.to_checksum_address(disperse_contract_address), abi=disperse_abi)

def disperse_ether(recipients, values):
    main_wallet_address = main_wallet['address']
    main_private_key = main_wallet['private_key']
    nonce = web3.eth.get_transaction_count(main_wallet_address)
    tx = disperse_contract.functions.disperseEther(recipients, values).build_transaction({
        'chainId': 1,
        'gasPrice': gas_price,
        'nonce': nonce,
        'value': sum(values)
    })
    gas_limit = web3.eth.estimate_gas(tx)
    tx ['gas'] = gas_limit

    signed_tx = web3.eth.account.sign_transaction(tx, main_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Ether transaction sent: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")

def disperse_tokens(token_address, recipients, values):
    main_wallet_address = main_wallet['address']
    main_private_key = main_wallet['private_key']
    nonce = web3.eth.get_transaction_count(main_wallet_address)
    tx = disperse_contract.functions.disperseToken(token_address, recipients, values).build_transaction({
        'chainId': 1,
        'gasPrice': gas_price,
        'nonce': nonce
    })
    gas_limit = web3.eth.estimate_gas(tx)
    tx ['gas'] = gas_limit

    signed_tx = web3.eth.account.sign_transaction(tx, main_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Token transaction sent: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")

def consolidate_eth(wallet, target_wallet):
    address = wallet['address']
    private_key = wallet['private_key']

    balance = web3.eth.get_balance(address)
    gas_fee = gas_price * gas_limit
    amount_to_send = balance - gas_fee #clears all wallets to 0 ether balance

    if amount_to_send <= 0:
        print(f"Insufficient balance in wallet {address} for the transaction.")
        return

    nonce = web3.eth.get_transaction_count(address)
    tx = {
        'chainId': 1,
        'nonce': nonce,
        'to': target_wallet,
        'value': amount_to_send,
        'gas': gas_limit,
        'gasPrice': gas_price,
    }

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction complete for wallet {address}: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")

def send_message(main_wallet, message, addresses, num_messages):
    main_wallet_address = main_wallet['address']
    main_wallet_private_key = main_wallet['private_key']

    hex_message = Web3.to_hex(text=message)

    message_gas_limit = 30000

    valid_addresses = []
    for address in addresses:
        address = address.strip()

        if address.endswith('.eth'):
            try:
                resolved_address = web3.ens.address(address)
                if resolved_address:
                    valid_addresses.append(Web3.to_checksum_address(resolved_address))
                else:
                    print(f"Unable to resolve ENS address: {address}")
            except Exception as e:
                print(f"Error resolving ENS address {address}: {e}")
        elif Web3.is_address(address):
            valid_addresses.append(Web3.to_checksum_address(address))
        else:
            print(f"Invalid address skipped: {address}")

    for i, address in enumerate(valid_addresses):
        for j in range(num_messages):
            nonce = web3.eth.get_transaction_count(main_wallet_address) + (i * num_messages) + j
            tx = {
                'chainId': 1,
                'nonce': nonce,
                'to': address,
                'value': 0,
                'gas': message_gas_limit,
                'gasPrice': gas_price + (j * 1000000000),
                'data': hex_message,
            }
            
            signed_tx = web3.eth.account.sign_transaction(tx, main_wallet_private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Message '{message}' sent to {address}: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")

def main():
    choice = input("Enter 'ether' to disperse, 'tokens' to disperse, 'consolidate', or 'message': ")

    if choice == "ether":
        wallet_count = int(input(f"Number of wallets? (Max {len(wallets)}): "))
        selected_wallets = wallets[:wallet_count]
        recipients = [wallet['address'] for wallet in selected_wallets]
        ether_amount = float(input("Amount of ETH to each wallet: "))
        values = [web3.to_wei(ether_amount, 'ether')] * wallet_count
        disperse_ether(recipients, values)
    elif choice == "tokens":
        wallet_count = int(input(f"Number of wallets? (Max {len(wallets)}): "))
        selected_wallets = wallets[:wallet_count]
        recipients = [wallet['address'] for wallet in selected_wallets]
        token_address = input("Enter the ERC-20 token contract address: ")
        token_amount = float(input("Token amount to disperse to each wallet: "))
        values = [int(token_amount * (10 ** 18))] * wallet_count 
        disperse_tokens(Web3.to_checksum_address(token_address), recipients, values)
    elif choice == "consolidate":
        for wallet in wallets:
            consolidate_eth(wallet, target_wallet)
    elif choice == 'message':
        message = input("Enter the message: ").strip()
        addresses = input("Enter the recipient addresses separated by commas: ").strip().split(',')
        num_messages = int(input("Enter the number of times to send the message: ").strip())
        send_message(main_wallet, message, addresses, num_messages)
    else:
        print("Invalid choice. Exiting.")

main()
