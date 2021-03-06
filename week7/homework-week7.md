## 1. MATCHSUM 里面 pearl-summary是什么？为什么要找到pearl-summary？

+ **Pearl-Summary**指的是虽有较低的sentence-level分数，但有很高的summary-level分数，如作者所说，有沧海遗珠的意思。

+ 因为论文观测的大部分数据集的最佳摘要并不是由句子级摘要得分高的摘要结果组成，很大比例是珍珠摘要组成，珍珠摘要在选择最佳摘要里是一个重要的影响因素

## 2. 知识蒸馏里参数 T（temperature）的意义？

+ 参数T是为了让模型产出合适的概率分布结果
+ 因为大模型的Softmax输出概率里面包含丰富的信息，不是真值的那些类对应的概率和真值那一类的概率的相对大小关系也包含了很多大模型学习到的信息 所以需要参数T来调整输出的概率分布，而不是单单最大化真值那一类的概率

$$
q_i= \frac{exp(\frac{z_i}{T})}{\sum_jexp(\frac{z_j}{T})}
$$

+ 如果T接近于0，则最大的值会越近1，其它值会接近0，就会丢失一些信息。
+ 如果T越大，则输出的结果的分布越平缓，相当于平滑的一个作用，起到保留相似信息的作用。

## 3. TAPT（任务自适应预训练）是如何操作的？

+ 任务自适应预训练(Task-Adaptive Pretraining ，TAPT)，在做任务相关的数据集，先把训练数据都拿过作为无监督的没有标签的数据继续进行预训练）在原来停止的预训练的地方训练一会），然后再对特定任务进行finetune。

## 4. 从模型优化的角度，在推理阶段，如何更改MATCHSUM的孪生网络结构？

+ 在推理时候，原先需要原文输入到网络进行推理，再候选数据输入到网络进行推理，网络的参数量*2 优化：用一个网络，将原文和候选数据*batch_size 一起输入到一个网络进行推理







