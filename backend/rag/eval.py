import chromadb
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from ragas import evaluate
from datasets import Dataset
from ragas.metrics import context_precision, context_recall, faithfulness, answer_relevancy

# 加载测试知识test.csv
loader = CSVLoader(
    file_path = 'test.csv',
    encoding = "utf-8",
    csv_args = {'delimiter': ',', 'quotechar': '"', 'fieldnames':['q', 'a']})

data = loader.load()

# embedding进入向量数据库(chroma)
embeddings = OpenAIEmbeddings()
chroma_client = chromadb.PersistentClient(path='./chroma_db')

vs = Chroma.from_documents(
    documents=data,
    embedding=embeddings,
    client=chroma_client,
    collection_name = 'test_collection')

# 检索器
retriever = vs.as_retriever()

# 大模型
llm = ChatOpenAI(model_name = "gpt-3.5", temperature = 0)

# prompt模板
template = """您是一个用于问答任务的助手，请使用下面提供的上下文来回答问题，并保持简洁的答案。  
        Question: {question}   
        Context: {context}   
        Answer:  
        """
prompt = ChatPromptTemplate.from_template(template)

# RAG生成器
rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser())



questions = ["小规模转一般纳税人之后，企业的税务登记信息会变更吗（比如企业的纳税人识别号，公司的纳税人名称）？",
             "生产企业外购货物直接出口可以享受出口退税吗？",
             "总公司与重点人群签订劳动合同，员工实际在分公司工作，并由分公司为其缴纳社保，应当由总公司还是分公司享受税收政策？",
             "中国首都在哪里，有哪些名胜古迹可以参观呢？"]

ground_truths = [
    ["小规模转一般纳税人以后，不会变更公司的税务登记信息的，只是企业的资格认定信息中会有一般纳税人资格认定。"],
    ["生产企业外购货物直接出口是否享受出口退税首先看企业是否属于列名生产企业出口非自产货物适用免抵退政策，具体情况详见相关政策。"],
    ["对于与总公司签订劳动合同，分公司缴纳社保的情形，应当由总公司享受税收政策。"],
    ["中国的首都是北京。北京有颐和园、长城、故宫等著名的风景名胜区。"]]

answers = []
contexts = []

# 生成answer和context
for query in questions:
    answers.append(rag_chain.invoke(query))
    contexts.append([docs.page_content
    for docs in retriever.get_relevant_documents(query)])

# 构建ragas需要的输入信息
data = {
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truths": ground_truths
}

# 开始评估
dataset = Dataset.from_dict(data)
result = evaluate(
    dataset=dataset,
    metrics=[
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
],
)

# 评估结果输出到excel
df = result.to_pandas()
df.to_excel('eval_result.xlsx', index=False)