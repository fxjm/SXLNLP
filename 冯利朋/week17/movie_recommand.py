import openpyxl
import numpy as np
import time
from collections import defaultdict


def build_u2i_matrix(user_item_score_data_path, item_name_data_path, write_file=False):
    item_id_to_item_name = {}
    with open(item_name_data_path, encoding="ISO-8859-1") as f:
        for line in f:
            item_id, item_name = line.split("|")[:2]
            item_id = int(item_id)
            item_id_to_item_name[item_id] = item_name
    total_movie_count = len(item_id_to_item_name)
    print("total movie:", total_movie_count)

    user_to_rating = {}
    with open(user_item_score_data_path, encoding="ISO-8859-1") as f:
        for line in f:
            user_id, item_id, score, time_stamp = line.split("\t")
            user_id, item_id, score = int(user_id), int(item_id), int(score)
            if user_id not in user_to_rating:
                user_to_rating[user_id] = [0] * total_movie_count
            user_to_rating[user_id][item_id - 1] = score
    print("total user:", len(user_to_rating))

    if not write_file:
        return user_to_rating, item_id_to_item_name
    
    workbook = openpyxl.Workbook()
    sheet = workbook.create_sheet(index=0)
    header = ["user_id"] + [item_id_to_item_name[i + 1] for i in range(total_movie_count)]
    sheet.append(header)
    for i in range(len(user_to_rating)):
        line = [i + 1] + user_to_rating[i + 1]
        sheet.append(line)
    workbook.save("user_movie_rating.xlsx")
    return user_to_rating, item_id_to_item_name

def cosine_distance(vector1, vector2):
    ab = vector1.dot(vector2)
    a_norm = np.sqrt(np.sum(np.square(vector1)))
    b_norm = np.sqrt(np.sum(np.square(vector2)))
    return ab/(a_norm * b_norm)

def find_similar_item(user_to_rating):
    item_to_vector = {}
    total_user = len(user_to_rating)
    for user, user_rating in user_to_rating.items():
        for moive_id, score in enumerate(user_to_rating):
            moive_id += 1
            if moive_id not in item_to_vector:
                item_to_vector[moive_id] = [0] * (total_user + 1)
            item_to_vector[moive_id][user] = score
    return find_similar_user(item_to_vector)

def find_similar_user(user_to_rating):
    user_to_similar_user = {}
    score_buffer = {}
    for user_a, ratings_a in user_to_rating.items():
        similar_user = []
        for user_b, ratings_b in user_to_rating.items():
            #全算比较慢，省去一部分用户
            if user_b == user_a or user_b > 100 or user_a > 100:
                continue
            #ab用户互换不用重新计算cos
            if "%d_%d"%(user_b, user_a) in score_buffer:
                similarity = score_buffer["%d_%d"%(user_b, user_a)]
            #相似度计算采取cos距离
            else:
                similarity = cosine_distance(np.array(ratings_a), np.array(ratings_b))
                score_buffer["%d_%d" % (user_a, user_b)] = similarity
            similar_user.append([user_b, similarity])
        similar_user = sorted(similar_user, reverse=True, key=lambda x:x[1])
        user_to_similar_user[user_a] = similar_user
    return user_to_similar_user


def user_cf(user_id, item_id, user_to_similar_user, user_to_rating, topn=10):
    pred_score = 0
    count = 0
    for similar_user, similarity in user_to_similar_user[user_id][:topn]:
        #相似用户对这部电影的打分
        rating_by_similiar_user = user_to_rating[similar_user][item_id - 1]
        #分数*用户相似度，作为一种对分数的加权，越相似的用户评分越重要
        pred_score += rating_by_similiar_user * similarity
        #如果这个相似用户没看过，就不计算在总数内
        if rating_by_similiar_user != 0:
            count += 1
    pred_score /= count + 1e-5
    return pred_score



def item_cf(user_id, item_id, similar_items, user_to_rating):
    pass

def movie_recommand(user_id, similar_user, similar_items, user_to_rating, item_to_name, topn=10):
    #当前用户还没看过的所有电影id
    unseen_items = [item_id + 1 for item_id, rating in enumerate(user_to_rating[user_id]) if rating == 0]
    res = []
    for item_id in unseen_items:
        #user_cf打分
        score = user_cf(user_id, item_id, similar_user, user_to_rating)
        # item_cf打分
        # score = item_cf(user_id, item_id, similar_items, user_to_rating)
        res.append([item_to_name[item_id], score])
    #排序输出
    res = sorted(res, key=lambda x:x[1], reverse=True)
    return res[:topn]



if __name__ == "__main__":
    user_item_score_data_path = "ml-100k/u.data"
    item_name_data_path = "ml-100k/u.item"
    user_to_rating, item_to_name = build_u2i_matrix(user_item_score_data_path, item_name_data_path, False)

    #user-cf
    similar_user = find_similar_user(user_to_rating)
    similar_items = find_similar_item(user_to_rating)


    #为用户推荐电影
    while True:
        user_id = int(input("输入用户id："))
        recommands = movie_recommand(user_id, similar_user, similar_items, user_to_rating, item_to_name)
        for recommand, score in recommands:
            print("%.4f\t%s"%(score, recommand))

