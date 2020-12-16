from elasticsearch import Elasticsearch
import xmltodict
import pandas as pd



def load_data(file):
    df = pd.read_csv("./data/sephora_website_dataset.csv")
    select = ['id', 'brand', 'category', 'name', 'size', 'rating',
       'number_of_reviews', 'love', 'price', 'URL', 'details',
       'how_to_use', 'ingredients']
    df = df[select]
    df["body"] = (df.brand + " " + df.name + " "+ df.details +" "+ df.how_to_use)
    return df

def get_prod_info(df, i):
    content = {"brand": df.iloc[i].brand,
            "category": df.iloc[i].category,
            "name": df.iloc[i]["name"],
            "rating": df.iloc[i].rating,
            "love": df.iloc[i].love,
            "price": df.iloc[i].price,
            "url": df.iloc[i].URL,
            "details": df.iloc[i].body,
            "ingredients": df.iloc[i].ingredients}
    return content

def index_sephora(es):
    if es.indices.exists(index='sephora'):
        res = "Index 'sephora' already exists, skip indexing."
        print(res)
        return res
    print("Loading data...")    
    df = df = load_data("./data/sephora_website_dataset.csv")
    
    print("Indexing sephora ...")
    for i in range(df.shape[0]):
        product_id = df.iloc[i].id
        content = get_prod_info(df, i)
        es.index(index='sephora', id=product_id, body=content)
    res = "Indexing completed."
    print(res)
    return res



def search_query(es, query, size, param):
    body = {
        "from":0,
        "size": size,
        "query": {
            "match": {
                param:query
            }
        }
    }

    res = es.search(index="sephora", body=body)
    print("Top", size, "results for query:", query[:100] )
    ids, scores = [], []
    for hit in res['hits']['hits']:
        i, score = hit['_id'], hit['_score']
        ids.append(i)
        scores.append(score)

        source = es.get(index="sephora", id=i)['_source']
        title = source['brand'] + " | " + source['name']
        
        print(i, score, title, sep="\t")
        
    return ids, scores



def get_product_result(es, query, size):
    ids, scores = search_query(es, query, size, "details")
    result = {}
    for pid in ids:
        result[pid] = es.get(index="sephora", id=pid)['_source']
    return result

def get_similar_product(es, id):
    ingredients = es.get(index="sephora", id=id)['_source']["ingredients"]
    ids, scores = search_query(es, ingredients, 5, "ingredients")
    result = {}
    for pid in ids:
        if pid==id: continue
        result[pid] = es.get(index="sephora", id=pid)['_source']
    return result






if __name__ == "__main__":
    
    es = Elasticsearch()
    index_sephora(es)
    # search_query(es, "skin care for men", 10, "details")
    res = get_similar_product(es, 1866706)
    # p = get_product_by_id(df, 1866706)
    # print(p)

    