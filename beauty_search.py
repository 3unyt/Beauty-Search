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
    product = {"brand": df.iloc[i].brand,
            "category": df.iloc[i].category,
            "name": df.iloc[i]["name"],
            "rating": df.iloc[i].rating,
            "love": df.iloc[i].love,
            "price": df.iloc[i].price,
            "url": df.iloc[i].URL,
            "details": df.iloc[i].details,
            "content": df.iloc[i].content,
            "ingredients": df.iloc[i].ingredients}
    return product

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



def basic_search(es, query, size):
    body = {
        "from":0,
        "size": size,
        "query" : {
            "multi_match": { 
                "query" : query,
                "type" : "cross_fields",
                "fields" : [ "brand^2", "name^2", "category^2", "details", "how_to_use"],
            }    
        },

        "highlight" : {
            "pre_tags" : ["<b>"],
            "post_tags" : ["</b>"],
            "fields" : {
                "details" : {}
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

def ingredients_search(es, query_ingredient, query_brand, size, exlude_brand=False):
    if exlude_brand:
        query={ 
            "bool": { 
                "must":{ 
                    "match": { "ingredients": query_ingredient }
                },
                "must_not": {
                    "match":  { "brand": query_brand }
                }
            }
        }
    else:
        query = {
            "match": {
                "ingredients": {
                    "query": query_ingredient,
                    "analyzer": "stop",
                    "zero_terms_query": "all",
                    "minimum_should_match": "50%"
                },
            },
        }
    body = {
        "from":0,
        "size": size,
        "query": query,
        "highlight" : {
            "pre_tags" : ["<mark>"],
            "post_tags" : ["</mark>"],
            "fields" : {
                "ingredients" : {}
            }
        }
    }
    res = es.search(index="sephora", body=body)
    return res['hits']['hits']


def get_product_result(es, query, size):
    hits = basic_search(es, query, size)
    result = {}
    for hit in hits:
        pid = hit['_id']
        result[pid] = hit['_source']
        description = hit['_source']['details'].split(".")[0]
        description = description.split(":")[1]
        description = "What it is: "+description+"."
        result[pid]["description"] = description
        
    return result

def get_similar_product(es, id):
    query_source = es.get(index="sephora", id=id)['_source']
    query_ingredients = query_source["ingredients"]
    query_brand = query_source['brand']
    hits = ingredients_search(es, query_ingredients, query_brand, 5)
    sim_result = {}
    same_brand_count = 0
    for hit in hits:
        if same_brand_count > 2:
            break
        pid, source = hit['_id'], hit['_source']
        if source["brand"] == query_source["brand"]:
            same_brand_count += 1 
        sim_result[pid] = source
        sim_result[pid]['highlight'] = hit['highlight']['ingredients'][0]
    
    if len(sim_result)==5:
        return sim_result

    ## get new hits that are from different brand
    new_hits = ingredients_search(es, query_ingredients, query_brand, 2, exlude_brand=True)
    for hit in new_hits:
        pid, source = hit['_id'], hit['_source']
        sim_result[pid] = source
        sim_result[pid]['highlight'] = hit['highlight']['ingredients'][0]

    
    return sim_result






if __name__ == "__main__":
    
    es = Elasticsearch()
    index_sephora(es)


    