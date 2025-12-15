import requests

def get_ID(list_of_URLs):
    ID_list = []

    for link in list_of_URLs:
        curr = requests.get(link)
        data = curr.json()["Data"]

        for key, value in data.items():
            ID_list.append(value["111752"])
        # Get price out of here as well?
    return ID_list
    



def main():
    test = ["https://www.bondsupermart.com/main/ws/v1/bond-exchange/bond/price?symbolList=8000.9.INFOUS0053830,8000.9.FINSFR0051264,8000.9.FINSUK0054442,8000.9.FINSHK0054075,8000.9.FINSUK0053980,8000.9.FINSUK0033821,8000.9.GOVTFEY0001389,8000.9.GOVTFEY0001498,8000.9.GOVTFEY0001593,8000.9.GOVTMY0018201"]
    print(get_ID(test))

if __name__ == "__main__":
    main()
