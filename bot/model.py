import multiprocessing
import neat
import os
import pickle
import simulation
import visualize
import random

RUNS_PER_NET = 1
START_BALANCE = 1000
SIM_MINUTES = 60 * 6
STARTING_POINT = random.random()
while STARTING_POINT < 0.2 or STARTING_POINT > 0.8:
    STARTING_POINT = random.random()
print(f"STARTING_POINT value: {STARTING_POINT}")

seed = random.randint(0, 1000)
print(f"SEED: {seed}")
random.seed(seed)

pool_size = multiprocessing.cpu_count() - 1
print(f"POOL SIZE: {pool_size}")


def eval_genome(genome, config):
    net = neat.nn.RecurrentNetwork.create(genome, config)

    fitnesses = []

    for runs in range(RUNS_PER_NET):
        sim = simulation.MarketSim(SIM_MINUTES, STARTING_POINT, START_BALANCE)
        net.reset()

        fitness = 0.00

        while not sim.done:
            inputs = sim.getState()
            action = net.activate(inputs)
            trade = simulation.getTrade(action)
            sim.step(trade)

            if sim.balance <= (START_BALANCE/2) and sim.holding == 0:
                break

            fitness = sim.getFitness()

        fitnesses.append(fitness)

    worst = min(fitnesses)
    return worst


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        genome.fitness = eval_genome(genome, config)


def run():
    # Load the config file, which is assumed to live in
    # the same directory as this script.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config')
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)

    pop = neat.Population(config)
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.StdOutReporter(True))

    pe = neat.ParallelEvaluator(multiprocessing.cpu_count() - 1, eval_genome)
    winner = pop.run(pe.evaluate, 3)

    # Save the winner.
    with open('winner-rnn', 'wb') as f:
        pickle.dump(winner, f)

    print(winner)

    visualize.plot_stats(stats, ylog=True, view=True, filename="rnn-fitness.svg")
    visualize.plot_species(stats, view=True, filename="rnn-speciation.svg")

    node_names = {-1: 'x', -2: 'dx', -3: 'theta', -4: 'dtheta', 0: 'control'}
    visualize.draw_net(config, winner, True, node_names=node_names)


if __name__ == '__main__':
    run()
