#ifndef H2O_GBMMOJOMODEL_H
#define H2O_GBMMOJOMODEL_H 1

#include "h2o/SharedTreeMojoModel.h"
#include "h2o/DistributionFamily.h"
#include "h2o/MojoReaderBackend.h"

#include <cassert>

namespace h2o {

class GbmMojoModel : public SharedTreeMojoModel {
public:

private:
    DistributionFamily *_family;
    double _init_f;

    // Disable copy constructor for now since _family is a pointer.
    GbmMojoModel (const GbmMojoModel &rhs);

public:
    GbmMojoModel() :
        _family(NULL)
    {}

    virtual ~GbmMojoModel() {
        if (_family != NULL) {
            delete _family;  _family = NULL;
        }
    }

    virtual void read(MojoReaderBackend &be) {
        SharedTreeMojoModel::readTreeCommon(be);
        std::string familyName = safeGetStringProperty("distribution");
        _family = DistributionFamily::valueOf(familyName);
        _init_f = safeGetDoubleProperty("init_f");
    }

    double *score0(double *row, double offset, double *preds) {
        scoreAllTrees(row, preds);
        if (_family->family() == bernoulli || _family->family() == modified_huber) {
            double f = preds[1] + _init_f + offset;
            preds[2] = _family->linkInv(f);
            preds[1] = 1.0 - preds[2];
        } else if (_family->family() == multinomial) {
            if (nclasses() == 2) { // 1-tree optimization for binomial
                preds[1] += _init_f + offset; //offset is not yet allowed, but added here to be future-proof
                preds[2] = -preds[1];
            }
            assert(0);
            // GenModel.GBM_rescale(preds);
        } else { // Regression
            double f = preds[0] + _init_f + offset;
            preds[0] = _family->linkInv(f);
            return preds;
        }
        if (balanceClasses()) {
            assert(0);
            // GenModel.correctProbabilities(preds, _priorClassDistrib, _modelClassDistrib);
        }
        assert(0);
        // preds[0] = GenModel.getPrediction(preds, _priorClassDistrib, row, _defaultThreshold);
        return preds;
    }

    virtual double *score0(double *row, double *preds) {
        return score0(row, 0.0, preds);
    }
};

}

#endif