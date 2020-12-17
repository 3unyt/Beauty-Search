from elasticsearch import Elasticsearch
import xmltodict
import pandas as pd



def load_data(file):
    df = pd.read_csv("./data/sephora_website_dataset.csv")
    select = ['id', 'brand', 'category', 'name', 'size', 'rating',
       'number_of_reviews', 'love', 'price', 'URL', 'details',
       'how_to_use', 'ingredients']
    df = df[select]
    df["content"] = (df.brand + " " + df.name + " " + df.category + " " + df.details +" "+ df.how_to_use)
    return df

def get_prod_info(df, i):
    content = {"brand": df.iloc[i].brand,
            "category": df.iloc[i].category,
            "name": df.iloc[i]["name"],
            "rating": df.iloc[i].rating,
            "love": df.iloc[i].love,
            "price": df.iloc[i].price,
            "url": df.iloc[i].URL,
            "details": df.iloc[i].details,
            "content": df.iloc[i].content,
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
        product = get_prod_info(df, i)
        es.index(index='sephora', id=product_id, body=product)
    res = "Indexing completed."
    print(res)
    return res



def search_query(es, query, size, field):
    body = {
        "from":0,
        "size": size,
        "query" : {
            "match": { field: query }
        },
        "highlight" : {
            "pre_tags" : ["<mark>"],
            "post_tags" : ["</mark>"],
            "fields" : {
                field : {}
            }
        }
    }

    res = es.search(index="sephora", body=body)
    print("Top", size, "results for query:", query[:100] )

    for hit in res['hits']['hits']:
        i, score = hit['_id'], hit['_score']
        source = hit['_source']
        title = source['brand'] + " | " + source['name']
        
        print(i, score, title, sep="\t")
        
    return res['hits']['hits']



def get_product_result(es, query, size):
    hits = search_query(es, query, size, "content")
    result = {}
    for hit in hits:
        pid = hit['_id']
        result[pid] = hit['_source']
        result[pid]['highlight'] = hit['highlight']['content'][0]
    return result

def get_similar_product(es, id):
    ingredients = es.get(index="sephora", id=id)['_source']["ingredients"]
    hits = search_query(es, ingredients, 5, "ingredients")
    sim_result = {}
    for hit in hits:
        pid = hit['_id']
        if pid==id: continue
        sim_result[pid] = hit['_source']
        sim_result[pid]['highlight'] = hit['highlight']['ingredients'][0]
    
    return sim_result






if __name__ == "__main__":
    
    es = Elasticsearch()
    index_sephora(es)
    # search_query(es, "skin care for men", 10, "details_combo")
    # res = get_similar_product(es, 1866706)
    # print(p)

    