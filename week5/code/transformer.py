import tensorflow as tf
from src.pgn_transformer_tf2.layers.position import positional_encoding
from src.utils.wv_loader import load_embedding_matrix


def create_padding_mask(seq):
    seq = tf.cast(tf.math.equal(seq, 0), tf.float32)

    # 添加额外的维度来将填充加到
    # 注意力对数（logits）。
    return seq[:, tf.newaxis, tf.newaxis, :]  # (batch_size, 1, 1, seq_len)


def create_look_ahead_mask(size):
    mask = 1 - tf.linalg.band_part(tf.ones((size, size)), -1, 0)
    return mask  # (seq_len, seq_len)


"""
create_look_ahead_mask
    [[0., 1., 1., 1.],
    [0., 0., 1., 1.],
    [0., 0., 0., 1.],
    [0., 0., 0., 0.]]
"""


def scaled_dot_product_attention(q, k, v, mask):
    """计算注意力权重。
    q, k, v 必须具有匹配的前置维度。
    k, v 必须有匹配的倒数第二个维度，例如：seq_len_k = seq_len_v。
    虽然 mask 根据其类型（填充或前瞻）有不同的形状，
    但是 mask 必须能进行广播转换以便求和。
    
    参数:
        q: 请求的形状 == (..., seq_len_q, depth)
        k: 主键的形状 == (..., seq_len_k, depth)
        v: 数值的形状 == (..., seq_len_v, depth_v)
        mask: Float 张量，其形状能转换成
            (..., seq_len_q, seq_len_k)。默认为None。
        
    返回值:
        输出，注意力权重
    """

    # ------------------------------------------------------------------------------
    # 补全代码
    # 使用 matmul 计算 q 和 k， 得到结果 matmul_qk
    # 缩放 matmul_qk
    # 使用根号 k 缩放 matmul_qk，注意要先对 k 值进行类型转换，得到 scaled_attention_logits
    # ------------------------------------------------------------------------------
    matmul_qk = tf.matmul(q, k, transpose_b=True)
    dk = tf.cast(tf.shape(k)[-1], tf.float32)
    scaled_attention_logits = matmul_qk / tf.math.sqrt(dk)

    # 将 mask 加入到缩放的张量上。
    if mask is not None:
        scaled_attention_logits += (mask * -1e9)

    # ------------------------------------------------------------------------------
    # 补全代码
    # 对 scaled_attention_logits 做 softmax 操作，得到注意力权重 attention_weights
    # 使用 attention_weights 对 v 做加权求和
    # ------------------------------------------------------------------------------
    attention_weights = tf.nn.softmax(scaled_attention_logits, axis=-1)
    output = tf.matmul(attention_weights, v)

    return output, attention_weights


class MultiHeadAttention(tf.keras.layers.Layer):
    def __init__(self, d_model, num_heads):
        super(MultiHeadAttention, self).__init__()
        self.num_heads = num_heads
        self.d_model = d_model

        assert d_model % self.num_heads == 0

        self.depth = d_model // self.num_heads

        self.wq = tf.keras.layers.Dense(d_model)
        self.wk = tf.keras.layers.Dense(d_model)
        self.wv = tf.keras.layers.Dense(d_model)

        self.dense = tf.keras.layers.Dense(d_model)

    def split_heads(self, x, batch_size):
        """分拆最后一个维度到 (num_heads, depth).
        转置结果使得形状为 (batch_size, num_heads, seq_len, depth)
        """
        x = tf.reshape(x, (batch_size, -1, self.num_heads, self.depth))
        return tf.transpose(x, perm=[0, 2, 1, 3])

    def call(self, v, k, q, mask):
        batch_size = tf.shape(q)[0]

        q = self.wq(q)  # (batch_size, seq_len, d_model)
        k = self.wk(k)  # (batch_size, seq_len, d_model)
        v = self.wv(v)  # (batch_size, seq_len, d_model)
        # ----------------------------------------------------------------------------------------
        # 补全代码
        # 分别对 q、k、v 使用 self.split_heads 函数，分拆成多头
        # 使用 scaled_dot_product_attention 函数计算注意力，得到 scaled_attention 和 attention_weights
        # ----------------------------------------------------------------------------------------
        split_q = self.split_heads(q, batch_size)
        split_k = self.split_heads(k, batch_size)
        split_v = self.split_heads(v, batch_size)
        scaled_attention, attention_weights = scaled_dot_product_attention(split_q, split_k, split_v, mask)

        scaled_attention = tf.transpose(scaled_attention,
                                        perm=[0, 2, 1, 3])  # (batch_size, seq_len_q, num_heads, depth)

        concat_attention = tf.reshape(scaled_attention,
                                      (batch_size, -1, self.d_model))  # (batch_size, seq_len_q, d_model)

        output = self.dense(concat_attention)  # (batch_size, seq_len_q, d_model)

        return output, attention_weights


# class Embedding(tf.keras.layers.Layer):
#
#     def __init__(self, params):
#         super(Embedding, self).__init__()
#         self.d_model = params['d_model']
#         embedding_matrix = load_embedding_matrix(max_vocab_size=params['vocab_size'])
#         self.vocab_size, self.embedding_dim = embedding_matrix.shape
#
#         self.embedding = tf.keras.layers.Embedding(self.vocab_size, self.embedding_dim,
#                                                    weights=[embedding_matrix], trainable=False)
#         self.pos_encoding = positional_encoding(self.vocab_size, self.embedding_dim)
#         self.fc = tf.keras.layers.Dense(self.d_model, activation='relu')
#
#     def call(self, x):
#         embed_x = self.embedding(x)  # (batch_size, target_seq_len, d_model)
#         embed_x *= tf.math.sqrt(tf.cast(self.d_model, tf.float32))
#         embed_x += self.pos_encoding[:, :tf.shape(x)[1], :]
#         return self.fc(embed_x)

class Embedding(tf.keras.layers.Layer):

    def __init__(self, vocab_size, d_model):
        super(Embedding, self).__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model

        self.embedding = tf.keras.layers.Embedding(vocab_size, d_model)
        self.pos_encoding = positional_encoding(vocab_size, d_model)

    def call(self, x):
        embed_x = self.embedding(x)  # (batch_size, target_seq_len, d_model)
        embed_x *= tf.math.sqrt(tf.cast(self.d_model, tf.float32))
        embed_x += self.pos_encoding[:, :tf.shape(x)[1], :]
        return embed_x


def create_masks(inp, tar):
    # 编码器填充遮挡
    enc_padding_mask = create_padding_mask(inp)

    # 在解码器的第二个注意力模块使用。
    # 该填充遮挡用于遮挡编码器的输出。
    dec_padding_mask = create_padding_mask(inp)

    # 在解码器的第一个注意力模块使用。
    # 用于填充（pad）和遮挡（mask）解码器获取到的输入的后续标记（future tokens）。
    look_ahead_mask = create_look_ahead_mask(tf.shape(tar)[1])
    dec_target_padding_mask = create_padding_mask(tar)
    combined_mask = tf.maximum(dec_target_padding_mask, look_ahead_mask)

    return enc_padding_mask, combined_mask, dec_padding_mask


if __name__ == '__main__':
    temp_mha = MultiHeadAttention(d_model=512, num_heads=8)
    y = tf.random.uniform((1, 60, 512))  # (batch_size, encoder_sequence, d_model)
    out, attn = temp_mha(y, k=y, q=y, mask=None)
    print(out.shape, attn.shape)
