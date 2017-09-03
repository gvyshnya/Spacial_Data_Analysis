library (readr)
library(plyr)
library(dplyr)
library(ggplot2)

library(cluster)
library(factoextra)
library(NbClust)
library(clValid)
library(fpc)

########################
### Read in the data ###
########################
fname_copper_clients <- "output/copper_customers_gated_final.csv"
fname_fibre_clients <- "output/fibre_customers_gated_final.csv"
fname_takeup <- "output/gated_community_take_up_ratios.csv"

df_fibre <- read_csv(fname_fibre_clients)
df_copper <- read_csv(fname_copper_clients)

View(df_fibre)

# split fiber customer by gated and non-gated communities
df_fibre_gated <- subset(df_fibre, df_fibre$gated_community_id > -1)
df_fibre_non_gated <- subset(df_fibre, df_fibre$gated_community_id == -1)

# split copper customer by gated and non-gated communities
df_copper_gated <- subset(df_copper, df_copper$gated_community_id > -1)
df_copper_non_gated <- subset(df_copper, df_copper$gated_community_id == -1)

# Fiber clients by community type

community_type <- c("Gated", "Non-Gated")
fiber_clients <- c(nrow(df_fibre_gated), nrow(df_fibre_non_gated))

total_community.data <- data.frame(community_type, fiber_clients)

ggplot(data=total_community.data, aes(x=community_type, y=fiber_clients, fill=fiber_clients)) +
  geom_bar(colour="black", stat="identity") +
  guides(fill=FALSE) +
  xlab("Type of Community") + ylab("Total clients") +
  ggtitle("Fibre Clients by Community Type")

# Copper Clients by community type
copper_clients <- c(nrow(df_copper_gated), nrow(df_copper_non_gated))

total_copper_community.data <- data.frame(community_type, copper_clients)

ggplot(data=total_copper_community.data, aes(x=community_type, y=copper_clients, fill=copper_clients)) +
  geom_bar(colour="black", stat="identity") +
  guides(fill=FALSE) +
  xlab("Type of Community") + ylab("Total clients") +
  ggtitle("Copper Clients by Community Type")

# count of fiber service clients by gated community
df_fiber_by_gated_community <- select(df_fibre_gated, gated_community_id) %>% add_count(gated_community_id)
df_fiber_by_gated_community <- unique(df_fiber_by_gated_community)
df_fiber_by_gated_community$fiber_clients <- df_fiber_by_gated_community$n
df_fiber_by_gated_community <- select(df_fiber_by_gated_community, gated_community_id, fiber_clients)
View(df_fiber_by_gated_community)

# count of copper service clients by gated community
df_copper_by_gated_community <- select(df_copper_gated, gated_community_id) %>% add_count(gated_community_id)
df_copper_by_gated_community <- unique(df_copper_by_gated_community)
df_copper_by_gated_community$copper_clients <- df_copper_by_gated_community$n
df_copper_by_gated_community <- select(df_copper_by_gated_community, gated_community_id, copper_clients)
View(df_copper_by_gated_community)

df_gated_community_customers <-merge(x=df_copper_by_gated_community,
                                     y=df_fiber_by_gated_community,
                                     by="gated_community_id",all.x=TRUE)
# fill resulted NA with 0
df_gated_community_customers[is.na(df_gated_community_customers)] <- 0

# add take-up ratio details for gated communities that we have client data for
df_takeup <- read_csv(fname_takeup)
df_gated_community_customers <- merge(x = df_gated_community_customers,
                                      y = df_takeup,
                                      by = "gated_community_id", all.x=TRUE)

# fill resulted NA with 0
df_gated_community_customers[is.na(df_gated_community_customers)] <- 0

View(df_gated_community_customers)

##################################################################
# Clustering Analysis of Customers by Gated Communities
##################################################################
# Steps:
# 1. Data preparation
# 2. Assessing clustering tendency (i.e., the clusterability of the data)
# 3. Defining the optimal number of clusters
# 4. Computing partitioning cluster analyses (e.g.: k-means, pam) or hierarchical clustering analyses
# 5. Validating clustering analyses: silhouette plot

# Scale variables
scaled_community_data <- select(df_gated_community_customers, 
                      total_unit, fiber_clients, copper_clients, take_up_ratio) %>% scale()
View(scaled_community_data)

# distance matrix
res.dist <- get_dist(scaled_community_data, stand = TRUE, method = "pearson")
fviz_dist(res.dist, 
          gradient = list(low = "#00AFBB", mid = "white", high = "#FC4E07"))

# Compute PAM
pam.res <- pam(scaled_community_data, 4)
# Visualize
fviz_cluster(pam.res)

# stability of clustering tendency

### Hopkins statistic: If the value of Hopkins statistic is close to zero (far below 0.5), 
### then we can conclude that the dataset is significantly clusterable.

### VAT (Visual Assessment of cluster Tendency): The VAT detects the clustering tendency in a 
### visual form by counting the number of square shaped dark (or colored) blocks along the diagonal 
## in a VAT image.
get_clust_tendency(scaled_community_data, n = 50,
                   gradient = list(low = "steelblue",  high = "white"))

# detecting the optimal number of clusters in k-mean
fviz_nbclust(scaled_community_data, kmeans, method = "gap_stat")

# detecting the optimal number of clusters
set.seed(123)
res.nbclust <- NbClust(scaled_community_data, distance = "euclidean",
                       min.nc = 2, max.nc = 10, 
                       method = "complete", index ="all") 

# visualizing it
factoextra::fviz_nbclust(res.nbclust) + theme_minimal()

# How to choose the appropriate clustering algorithms for your data?
intern <- clValid(scaled_community_data, nClust = 2:10, 
                  clMethods = c("hierarchical", "kmeans", "diana", "fanny", "model", 
                                "sota", "pam", "clara", "agnes"),
                  validation = "internal") 
# eliminate 'som'

# Summary
summary(intern) # hierarchical, 2 clusters

# Enhanced hierarchical clustering, cut in 2 groups
res.hc <- eclust(scaled_community_data, "hclust", k = 2, graph = FALSE) 
# Visualize 
fviz_dend(res.hc, rect = TRUE, show_labels = FALSE)

# validate the cluster - Visualize the silhouette plot
fviz_silhouette(res.hc)

# Silhouette coefficient of observations
sil <- silhouette(res.hc$cluster, dist(scaled_community_data))
head(sil[, 1:3], 10)

# Summary of silhouette analysis
si.sum <- summary(sil)
# Average silhouette width of each cluster
si.sum$clus.avg.widths

# The total average (mean of all individual silhouette widths)
si.sum$avg.width

# The size of each clusters
si.sum$clus.sizes

# Visualize clusters
fviz_cluster(res.hc, geom = "point", ellipse.type = "norm")

# cluser results per gated community
res.hc$cluster

df_gated_community_customers$cluster <- res.hc$cluster
View(df_gated_community_customers)

df_big_customer_communities <- subset(df_gated_community_customers, cluster == 1)
df_big_customer_communities <- select(df_big_customer_communities, -cluster)
View(df_big_customer_communities)
colnames(df_big_customer_communities)
