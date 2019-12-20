import multiprocessing
import neat
import os
import pickle
import simulation
import visualize

runs_per_net = 3
simulation_minutes = 60 * 1 # 24 hours in minutes


def eval_genome(genome, config):
    net = neat.nn.RecurrentNetwork.create(genome, config)

    fitnesses = []

    for runs in range(runs_per_net):
        sim = simulation.MarketSim(simulation_minutes)
        net.reset()

        fitness = sim.balance

        while not sim.done:
            inputs = sim.getState()
            action = net.activate(inputs)
            trade = simulation.getTrade(action)
            sim.step(trade)

            if sim.balance <= 500 and sim.holding == 0:
                break

            fitness = sim.balance

        fitnesses.append(fitness)

    return min(fitnesses)


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
