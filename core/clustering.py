"""
ABA利基分析工具 v5.0 - 语义聚类模块（兼容v4.0）
"""

import re
from collections import Counter
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np


class KeywordClusterer:
    """关键词聚类器"""
    
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.model = None
    
    def cluster(self, keywords: List[str]) -> Dict[int, List[str]]:
        """聚类关键词"""
        if len(keywords) < self.n_clusters:
            self.n_clusters = max(1, len(keywords) // 2)
        
        X = self.vectorizer.fit_transform(keywords)
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42)
        labels = self.model.fit_predict(X)
        
        result = {}
        for idx, label in enumerate(labels):
            if label not in result:
                result[label] = []
            result[label].append(keywords[idx])
        
        return result
    
    def get_cluster_centers(self) -> List[str]:
        """获取聚类中心关键词"""
        if self.model is None:
            return []
        
        feature_names = self.vectorizer.get_feature_names_out()
        centers = []
        for center in self.model.cluster_centers_:
            top_idx = np.argsort(center)[-5:]
            top_words = [feature_names[i] for i in top_idx]
            centers.append(" ".join(top_words))
        
        return centers
