import os
import shutil

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col

from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

spark = SparkSession.builder.appName("Group7").config("spark.driver.memoery", "4g").getOrCreate()
def create_dataframe() -> DataFrame:

    filepath = os.path.join("outputs", "work_df")
    spark_df = spark.read.parquet(filepath)
    colMap = {
        "userId": col("userId").cast("int"),
        "bookId": col("bookId").cast("int"),
        "rating": col("rating").cast("int")
    }
    spark_df = spark_df.withColumns(colMap)

    ratings_df = spark_df.select("userId", "bookId", "rating")
    return ratings_df

def create_model(evaluator) -> CrossValidator:

    als = ALS(
        userCol="userId",
        itemCol="bookId",
        ratingCol="rating",
        nonnegative=True,
        coldStartStrategy="drop",
        seed=42
    )

    param_grid = ParamGridBuilder() \
        .addGrid(als.maxIter, [5, 10]) \
        .addGrid(als.rank, [3, 5]) \
        .addGrid(als.regParam, [0.1, 0.2]) \
        .build()

    cv = CrossValidator(
        estimator=als,
        estimatorParamMaps=param_grid,
        evaluator=evaluator
    )

    return cv

def main() -> None:

    book_ratings = create_dataframe()
    (train, test) = book_ratings.randomSplit([0.8, 0.2], seed=42)

    evaluator = RegressionEvaluator(
        metricName="rmse",
        labelCol="rating",
        predictionCol="prediction"
    )
    model = create_model(evaluator=evaluator).fit(train)
    pred = model.bestModel.transform(test)

    if os.path.exists("alsrecommend.model"):
        shutil.rmtree("alsrecommend.model")
    model.bestModel.save("alsrecommend.model")

    spark.stop()


if __name__ == "__main__":
    main()
