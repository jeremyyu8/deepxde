from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import deepxde as dde
import matplotlib.pyplot as plt
from deepxde.backend import tf
import numpy as np


# generate num equally-spaced points from -1 to 1
def gen_traindata(num):
    xvals = np.linspace(-1, 1, num).reshape(num, 1)
    uvals = np.sin(np.pi * xvals)
    return xvals, uvals


def main():
    def pde(x, y):
        u, q = y[:, 0:1], y[:, 1:2]
        du_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)

        # solution is u(x) = sin(pi*x), q(x) = -pi^2 * sin(pi*x)
        return -du_xx + q

    def sol(x):
        return np.sin(np.pi * x ** 2)

    geom = dde.geometry.Interval(-1, 1)

    bc = dde.DirichletBC(geom, sol, lambda _, on_boundary: on_boundary, component=0)
    ob_x, ob_u = gen_traindata(100)
    observe_u = dde.PointSetBC(ob_x, ob_u, component=0)

    data = dde.data.PDE(
        geom,
        pde,
        [bc, observe_u],
        num_domain=200,
        num_boundary=50,
        anchors=ob_x,
        num_test=1000,
    )

    net = dde.maps.PFNN([1, [20, 20], [20, 20], [20, 20], 2], "tanh", "Glorot uniform")

    model = dde.Model(data, net)
    model.compile("adam", lr=0.0001, loss_weights=[1, 100, 1000])

    losshistory, train_state = model.train(epochs=20000)
    dde.saveplot(losshistory, train_state, issave=True, isplot=True)

    # view results
    x = geom.uniform_points(500)
    yhat = model.predict(x)
    uhat, qhat = yhat[:, 0:1], yhat[:, 1:2]

    utrue = np.sin(np.pi * x)
    print("l2 relative error for u: " + str(dde.metrics.l2_relative_error(utrue, uhat)))
    plot1 = plt.figure(3)
    plt.plot(x, uhat, label="uhat")
    plt.plot(x, utrue, label="utrue")
    plt.legend()

    qtrue = -np.pi ** 2 * np.sin(np.pi * x)
    print("l2 relative error for q: " + str(dde.metrics.l2_relative_error(qtrue, qhat)))
    plot2 = plt.figure(4)
    plt.plot(x, qhat, label="qhat")
    plt.plot(x, qtrue, label="qtrue")
    plt.legend()

    plt.show()


if __name__ == "__main__":
    main()
