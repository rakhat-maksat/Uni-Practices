import re
import json

def parse_receipt(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
    
    date_match = re.search(r'Date:\s*(\d{2}\.\d{2}\.\d{4})', text)
    date = date_match.group(1) if date_match else None
    
    time_match = re.search(r'Time:\s*(\d{2}:\d{2}:\d{2})', text)
    time = time_match.group(1) if time_match else None
    
    products = []
    product_pattern = r'([A-Za-z0-9\s.%]+?)\s+(\d+)\s*тг'
    matches = re.findall(product_pattern, text)
    
    for name, price in matches:
        if any(word in name.upper() for word in ['SUBTOTAL', 'VAT', 'TOTAL']):
            continue
        products.append({
            'name': name.strip(),
            'price': int(price)
        })
    
    total_match = re.search(r'TOTAL:\s*(\d+)\s*тг', text)
    total = int(total_match.group(1)) if total_match else None
    
    payment_match = re.search(r'Payment Method:\s*(\w+)', text)
    payment_method = payment_match.group(1) if payment_match else None
    
    card_match = re.search(r'Card:\s*([\*\s\d]+)', text)
    card = card_match.group(1).strip() if card_match else None
    
    receipt_data = {
        'date': date,
        'time': time,
        'products': products,
        'total': total,
        'payment_method': payment_method,
        'card': card
    }
    
    return receipt_data


def print_receipt(data):
    print("\n" + "="*50)
    print("           PARSED RECEIPT DATA")
    print("="*50)
    
    print(f"Date: {data['date'] if data['date'] else 'Not found'}")
    print(f"Time: {data['time'] if data['time'] else 'Not found'}")
    
    print("\nProducts:")
    print("-"*50)
    
    for product in data['products']:
        print(f"  {product['name']:<30} {product['price']:>6} тг")
    
    print("-"*50)
    
    if data['total'] is not None:
        print(f"{'TOTAL:':<32} {data['total']:>6} тг")
    else:
        print(f"{'TOTAL:':<32} Not found")
    
    print("\nPayment:")
    print(f"  Method: {data['payment_method'] if data['payment_method'] else 'Not found'}")
    
    if data['card']:
        print(f"  Card: {data['card']}")
    
    print("="*50 + "\n")


def save_to_json(data, filename="receipt_data.json"):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"Data saved to {filename}")


if __name__ == "__main__":
    receipt = parse_receipt("raw.txt")
    
    print_receipt(receipt)
    save_to_json(receipt)
    
    print("\nStatistics:")
    print(f"  Total items: {len(receipt['products'])}")
    
    if receipt['products']:
        avg_price = sum(p['price'] for p in receipt['products']) / len(receipt['products'])
        print(f"  Average price: {avg_price:.2f} тг")
        
        most_expensive = max(receipt['products'], key=lambda x: x['price'])
        print(f"  Most expensive: {most_expensive['name']} ({most_expensive['price']} тг)")