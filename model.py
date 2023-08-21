import tensorflow as tf


def DeepDRP(input_shape=(500, 1910)):
    inputs = tf.keras.layers.Input(shape=input_shape, name="inputs")
    masking = tf.keras.layers.Masking(input_shape=input_shape, mask_value=0)(inputs)

    x = tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(units=1024, activation="tanh"))(masking)
    x = tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(units=512, activation="tanh"))(x)
    x = tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(units=256, activation="tanh"))(x)

    x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(units=256, return_sequences=True, activation='tanh'))(x)
    x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(units=64, return_sequences=True, activation='tanh'))(x)
    x = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(units=2, return_sequences=True, activation='tanh'))(x)

    flatten = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(units=2048, activation="relu")(flatten)
    x = tf.keras.layers.Dense(units=1024, activation="relu")(x)
    outputs = tf.keras.layers.Dense(units=500, activation="sigmoid")(x)

    model = tf.keras.Model(inputs=[inputs], outputs=[outputs])
    model.compile(loss=tf.keras.losses.mse,
                  optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
                  )

    return model


model = DeepDRP((500, 1000))
model.summary()


