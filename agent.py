import torch
import random
import numpy as np
from collections import deque
from snake_gameai import SnakeGameAI, Direction, Point, BLOCK_SIZE
from model import Linear_QNet, QTrainer
from Helper import plot
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001


class Agent:
    def __init__(self):
        self.n_game = 0
        self.epsilon = 0  # Randomness
        self.gamma = 0.9  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()
        self.model = Linear_QNet(11, 256, 3)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
        # for n,p in self.model.named_parameters():
        #     print(p.device,'',n)
        # self.model.to('cuda')
        # for n,p in self.model.named_parameters():
        #     print(p.device,'',n)

    # state (11 Values)
    # [ danger straight, danger right, danger left,
    #
    # direction left, direction right,
    # direction up, direction down
    #
    # food left,food right,
    # food up, food down]
    def get_state(self, game):
        head = game.snake[0]
        point_l = Point(head.x - BLOCK_SIZE, head.y)
        point_r = Point(head.x + BLOCK_SIZE, head.y)
        point_u = Point(head.x, head.y - BLOCK_SIZE)
        point_d = Point(head.x, head.y + BLOCK_SIZE)

        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN

        state = [
            # Danger Straight
            (dir_u and game.is_collision(point_u)) or
            (dir_d and game.is_collision(point_d)) or
            (dir_l and game.is_collision(point_l)) or
            (dir_r and game.is_collision(point_r)),

            # Danger right
            (dir_u and game.is_collision(point_r)) or
            (dir_d and game.is_collision(point_l)) or
            (dir_u and game.is_collision(point_u)) or
            (dir_d and game.is_collision(point_d)),

            # Danger Left
            (dir_u and game.is_collision(point_r)) or
            (dir_d and game.is_collision(point_l)) or
            (dir_r and game.is_collision(point_u)) or
            (dir_l and game.is_collision(point_d)),

            # Move Direction
            dir_l,
            dir_r,
            dir_u,
            dir_d,

            # Food Location
            game.food.x < game.head.x,  # food is in left
            game.food.x > game.head.x,  # food is in right
            game.food.y < game.head.y,  # food is up
            game.food.y > game.head.y  # food is down
        ]
        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        # popleft if memory exceed
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if (len(self.memory) > BATCH_SIZE):
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory
        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    # TODO: What is the role of epsilon in this method? Feel free to reference the OpenAI Gym RL tutorial from 02/09/22
    """
    The role of epsilon is to introduce randomness, of choosing random instead of best action.
    This helps our model explore more to collect more and to allow the AI to explore other random
    options rather than the immediate best one, without heavily depending on the information it already has prior.
    In this specific method, higher epsilon equals more chance of exploration and more chance of random choice.
    """

    def get_action(self, state):
        # random moves: tradeoff explotation / exploitation
        self.epsilon = 80 - self.n_game
        final_move = [0, 0, 0]
        if(random.randint(0, 200) < self.epsilon):
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float).cpu()
            prediction = self.model(state0).cpu()  # prediction by model
            move = torch.argmax(prediction).item()
            final_move[move] = 1
        return final_move


# TODO: Write a couple sentences describing the training process coded below.
"""
This is where the program does most of the work.
This code below initalizes all variables. Sets the agent class and and game class.
The the while loop that cycles over after every move that:
- grabs the state of the game
- grabs the player movement
- performs the move
- grabs the updated and updated state of the game
After the infinite while loop comes and if statement that IF the game is 'done,' 
we train the long term memory, the game resets and prints its status, counts and updates total stats
and then repeats the loop all over again.
"""


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = SnakeGameAI()
    while True:
        # Get Old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(
            state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # Train long memory,plot result
            game.reset()
            agent.n_game += 1
            agent.train_long_memory()
            if(score > reward):  # new High score
                reward = score
                agent.model.save()
            print('Game:', agent.n_game, 'Score:', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_game
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if(__name__ == "__main__"):
    train()

# TODO: Write a brief paragraph on your thoughts about this implementation.
# Was there anything surprising, interesting, confusing, or clever? Does the code smell at all?
"""
I thought the code was very direct and simple.
It's very interesting to look at the script and dissect the mind of the program of how ti will perform and react.
I think overall, the implementtaion is really well thought out and well written regarding the implementation and view
of reinforcement learning. I'm sure there could be other technical improvements in regards to the coding aspect of it all,
but the code was great overall.
"""
