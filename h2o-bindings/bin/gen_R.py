#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import bindings as bi
import sys
PY3 = sys.version_info[0] == 3
str_type = str if PY3 else (str, unicode)

# ----------------------------------------------------------------------------------------------------------------------
#   Generate per-model classes
# ----------------------------------------------------------------------------------------------------------------------

def gen_module(schema, algo):
    help_preamble = help_preamble_for(algo)
    help_epilogue = help_epilogue_for(algo)
    help_afterword = help_afterword_for(algo)
    model_name = algo_to_modelname(algo)
    help_example = help_example_for(algo)
    help_return = help_return_for(algo)
    help_references = help_references_for(algo)
    class_extra = class_extra_for(algo)

    yield "# This file is auto-generated by h2o-3/h2o-bindings/bin/gen_R.py"
    yield "# Copyright 2016 H2O.ai;  Apache License Version 2.0 (see LICENSE for details) \n#'"
    yield "# -------------------------- %s -------------------------- #" % model_name
    if help_preamble:
        lines = help_preamble.split("\n")
        for line in lines:
            yield "#' %s" % line.lstrip()
    yield "#'"
    yield "#' @param x A vector containing the \code{character} names of the predictors in the model."
    yield "#'        If x is missing,then all columns except y are used."
    yield "#' @param y The name of the response variable in the model."
    for param in schema["parameters"]:
        if param["name"] == "ignored_columns" or param["name"] == "response_column":
            continue;
        phelp = param["help"]
        if param["type"] == "boolean":
            phelp = "\code{Logical}. " + phelp
        if param["values"]:
            phelp += " Must be one of: %s." % ", ".join('"%s"' % p for p in param["values"])
        if param["default_value"] is not None:
            phelp += " Defaults to %s." % param["default_value"]
        yield "#' @param %s %s" % (param["name"], bi.wrap(phelp, indent=("#'        "), indent_first=False))
    if help_return:
        yield "#' @return %s" % bi.wrap(help_return, indent=("#'          "), indent_first=False)
    if help_epilogue:
        yield "#' @seealso %s" % bi.wrap(help_epilogue, indent=("#'          "), indent_first=False)
    if help_references:
        #lines = help_references.split("\n")
        #for line in lines:
        #    yield "#' %s" % line.lstrip()
        yield "#' @references %s" % bi.wrap(help_references, indent=("#'             "), indent_first=False)
    if help_example:
        yield "#' @examples"
        lines = help_example.split("\n")
        for line in lines:
            yield "#' %s" % line.lstrip()
    yield "#' @export"
    yield "h2o.%s <- function(x, y, " % algo
    list = []
    for param in schema["parameters"]:
        if param["name"] == "ignored_columns" or param["name"] == "response_column":
            continue;
        if param["type"][:4] == "enum" or param["default_value"] is not None:
            list.append(indent("%s  = %s" % (param["name"], normalize_value(param)), 17 + len(algo)))
        else:
            list.append(indent(param["name"], 17 + len(algo)))
    yield ", \n".join(list)
    yield indent(") \n{", 17 + len(algo))
    yield "  #If x is missing, then assume user wants to use all columns as features."
    yield "  if(missing(x)){"
    yield "     if(is.numeric(y)){"
    yield "         x <- setdiff(col(training_frame),y)"
    yield "     }else{"
    yield "         x <- setdiff(colnames(training_frame),y)"
    yield "     }"
    yield "  }"
    yield ""
    yield "  # Required args: training_frame"
    yield "  if( missing(training_frame) ) stop(\"argument \'training_frame\' is missing, with no default\")"
    yield "  if( missing(validation_frame) ) validation_frame = NULL"
    yield "  # Training_frame and validation_frame may be a key or an H2OFrame object"
    yield "  if (!is.H2OFrame(training_frame))"
    yield "     tryCatch(training_frame <- h2o.getFrame(training_frame),"
    yield "           error = function(err) {"
    yield "             stop(\"argument \'training_frame\' must be a valid H2OFrame or key\")"
    yield "           })"
    yield "  if (!is.null(validation_frame)) {"
    yield "     if (!is.H2OFrame(validation_frame))"
    yield "         tryCatch(validation_frame <- h2o.getFrame(validation_frame),"
    yield "             error = function(err) {"
    yield "                 stop(\"argument \'validation_frame\' must be a valid H2OFrame or key\")"
    yield "             })"
    yield "  }"
    yield "  # Parameter list to send to model builder"
    yield "  parms <- list()"
    yield "  parms$training_frame <- training_frame"
    yield "  args <- .verify_dataxy(training_frame, x, y, autoencoder)"
    yield "  if( !missing(offset_column) && !is.null(offset_column))  args$x_ignore <- args$x_ignore[!( offset_column == args$x_ignore )]"
    yield "  if( !missing(weights_column) && !is.null(weights_column)) args$x_ignore <- args$x_ignore[!( weights_column == args$x_ignore )]"
    yield "  if( !missing(fold_column) && !is.null(fold_column)) args$x_ignore <- args$x_ignore[!( fold_column == args$x_ignore )]"
    yield "  parms$response_column <- args$y"
    yield "  parms$ignored_columns <- args$x_ignore \n "

    for param in schema["parameters"]:
        if param["name"] == "ignored_columns" or param["name"] == "response_column" or param["name"] == "training_frame":
            continue;
        if param["name"] == "loss":
            yield "  if(!missing(loss)) {"
            yield "    if(loss == \"MeanSquare\") {"
            yield "      warning(\"Loss name 'MeanSquare' is deprecated; please use 'Quadratic' instead.\")"
            yield "      parms$loss <- \"Quadratic\""
            yield "    } else "
            yield "      parms$loss <- loss"
            yield "  }"
        yield "  if (!missing(%s))" % param["name"]
        yield "    parms$%s <- %s" % (param["name"], param["name"])
    yield "  .h2o.modelJob('%s', parms, h2oRestApiVersion=3) \n}" % algo

    if help_afterword:
        lines = help_afterword.split("\n")
        for line in lines:
            yield "%s" % line.lstrip()
        #yield "%s" % bi.wrap(help_afterword, indent=("#' "), indent_first=True)

    if class_extra:
        yield class_extra

def normalize_value(param):
    if param["type"][:4] == "enum":
        return "c(%s)" % ", ".join('"%s"' % p for p in param["values"])
    if "[]" in param["type"]:
        return "c(%s)" % ", ".join('%s' % p for p in param["default_value"])
    if param["type"] == "boolean":
        return str(param["default_value"]).upper()
    return param["default_value"]

def indent(string, indent):
    return " " * indent + string;

def algo_to_modelname(algo):
    if algo == "deeplearning": return "Deep Learning - Neural Network"
    if algo == "deepwater": return "Deep Water - Neural Network"
    if algo == "gbm": return "Gradient Boosting Machine"
    if algo == "glm": return "H2O Generalized Linear Models"
    if algo == "glrm": return "Generalized Low Rank Model"
    if algo == "kmeans": return "KMeans Model in H2O"
    if algo == "naivebayes": return "Naive Bayes Model in H2O"
    if algo == "drf": return "Random Forest Model in H2O"
    if algo == "svd": return "Singular Value Decomposition"
    if algo == "pca": return "Principal Components Analysis"
    return algo

def help_preamble_for(algo):
    if algo == "deeplearning":
        return """
            Build a Deep Neural Network model using CPUs
            Builds a feed-forward multilayer artificial neural network on an H2OFrame"""
    if algo == "deepwater":
        return """
            Build a Deep Learning model using multiple native GPU backends
            Builds a deep neural network on an H2OFrame containing various data sources"""
    if algo == "kmeans":
        return """Performs k-means clustering on an H2O dataset."""
    if algo == "glrm":
        return """Builds a generalized low rank model of a H2O dataset."""
    if algo == "glm":
        return """
            Fits a generalized linear model, specified by a response variable, a set of predictors, and a
            description of the error distribution."""
    if algo == "gbm":
        return """
            Builds gradient boosted trees on a parsed data set, for regression or classification.
            The default distribution function will guess the model type based on the response column type.
            Otherwise, the response column must be an enum for "bernoulli" or "multinomial", and numeric
            for all other distributions."""
    if algo == "naivebayes":
        return """
            The naive Bayes classifier assumes independence between predictor variables
            conditional on the response, and a Gaussian distribution of numeric predictors with
            mean and standard deviation computed from the training dataset. When building a naive
            Bayes classifier, every row in the training dataset that contains at least one NA will
            be skipped completely. If the test dataset has missing values, then those predictors
            are omitted in the probability calculation during prediction."""

def help_epilogue_for(algo):
    if algo == "deeplearning":
        return """\code{\link{predict.H2OModel}} for prediction"""
    if algo == "glm":
        return """\code{\link{predict.H2OModel}} for prediction, \code{\link{h2o.mse}}, \code{\link{h2o.auc}}, \code{\link{h2o.confusionMatrix}}, \code{\link{h2o.performance}}, \code{\link{h2o.giniCoef}}, \code{\link{h2o.logloss}}, \code{\link{h2o.varimp}}, \code{\link{h2o.scoreHistory}}"""
    if algo == "glrm":
        return """\code{\link{h2o.kmeans}, \link{h2o.svd}}, \code{\link{h2o.prcomp}}"""

def help_return_for(algo):
    if algo == "glrm":
        return "Returns an object of class \linkS4class{H2ODimReductionModel}."

def help_references_for(algo):
    if algo == "glrm":
        return """M. Udell, C. Horn, R. Zadeh, S. Boyd (2014). {Generalized Low Rank Models}[http://arxiv.org/abs/1410.0342]. Unpublished manuscript, Stanford Electrical Engineering Department; N. Halko, P.G. Martinsson, J.A. Tropp. {Finding structure with randomness: Probabilistic algorithms for constructing approximate matrix decompositions}[http://arxiv.org/abs/0909.4061]. SIAM Rev., Survey and Review section, Vol. 53, num. 2, pp. 217-288, June 2011."""

def help_example_for(algo):
    if algo == "deeplearning":
        return """\donttest{
            library(h2o)
            h2o.init()
            iris.hex <- as.h2o(iris)
            iris.dl <- h2o.deeplearning(x = 1:4, y = 5, training_frame = iris.hex)

            # now make a prediction
            predictions <- h2o.predict(iris.dl, iris.hex)
            }"""
    if algo == "glm":
        return """\code{\link{predict.H2OModel}} for prediction, \code{\link{h2o.mse}}, \code{\link{h2o.auc}}, \code{\link{h2o.confusionMatrix}}, \code{\link{h2o.performance}}, \code{\link{h2o.giniCoef}}, \code{\link{h2o.logloss}}, \code{\link{h2o.varimp}}, \code{\link{h2o.scoreHistory}}"""
    if algo == "glrm":
        return """\donttest{
            library(h2o)
            h2o.init()
            ausPath <- system.file("extdata", "australia.csv", package="h2o")
            australia.hex <- h2o.uploadFile(path = ausPath)
            h2o.glrm(training_frame = australia.hex, k = 5, loss = "Quadratic", regularization_x = "L1",
            gamma_x = 0.5, gamma_y = 0, max_iterations = 1000)
            }"""

def help_afterword_for(algo):
    if algo == "deeplearning":
        return """
            #' Anomaly Detection via H2O Deep Learning Model
            #'
            #' Detect anomalies in an H2O dataset using an H2O deep learning model with
            #' auto-encoding.
            #'
            #' @param object An \linkS4class{H2OAutoEncoderModel} object that represents the
            #'        model to be used for anomaly detection.
            #' @param data An H2OFrame object.
            #' @param per_feature Whether to return the per-feature squared reconstruction error
            #' @return Returns an H2OFrame object containing the
            #'         reconstruction MSE or the per-feature squared error.
            #' @seealso \code{\link{h2o.deeplearning}} for making an H2OAutoEncoderModel.
            #' @examples
            #' \donttest{
            #' library(h2o)
            #' h2o.init()
            #' prosPath = system.file("extdata", "prostate.csv", package = "h2o")
            #' prostate.hex = h2o.importFile(path = prosPath)
            #' prostate.dl = h2o.deeplearning(x = 3:9, training_frame = prostate.hex, autoencoder = TRUE,
            #'                                hidden = c(10, 10), epochs = 5)
            #' prostate.anon = h2o.anomaly(prostate.dl, prostate.hex)
            #' head(prostate.anon)
            #' prostate.anon.per.feature = h2o.anomaly(prostate.dl, prostate.hex, per_feature=TRUE)
            #' head(prostate.anon.per.feature)
            #' }
            #' @export
            h2o.anomaly <- function(object, data, per_feature=FALSE) {
              url <- paste0('Predictions/models/', object@model_id, '/frames/',h2o.getId(data))
              res <- .h2o.__remoteSend(url, method = "POST", reconstruction_error=TRUE, reconstruction_error_per_feature=per_feature)
              key <- res$model_metrics[[1L]]$predictions$frame_id$name
              h2o.getFrame(key)
            }

            #' Feature Generation via H2O Deep Learning Model
            #'
            #' Extract the non-linear feature from an H2O data set using an H2O deep learning
            #' model.
            #' @param object An \linkS4class{H2OModel} object that represents the deep
            #' learning model to be used for feature extraction.
            #' @param data An H2OFrame object.
            #' @param layer Index of the hidden layer to extract.
            #' @return Returns an H2OFrame object with as many features as the
            #'         number of units in the hidden layer of the specified index.
            #' @seealso \code{link{h2o.deeplearning}} for making deep learning models.
            #' @examples
            #' \donttest{
            #' library(h2o)
            #' h2o.init()
            #' prosPath = system.file("extdata", "prostate.csv", package = "h2o")
            #' prostate.hex = h2o.importFile(path = prosPath)
            #' prostate.dl = h2o.deeplearning(x = 3:9, y = 2, training_frame = prostate.hex,
            #'                                hidden = c(100, 200), epochs = 5)
            #' prostate.deepfeatures_layer1 = h2o.deepfeatures(prostate.dl, prostate.hex, layer = 1)
            #' prostate.deepfeatures_layer2 = h2o.deepfeatures(prostate.dl, prostate.hex, layer = 2)
            #' head(prostate.deepfeatures_layer1)
            #' head(prostate.deepfeatures_layer2)
            #' }
            #' @export
            h2o.deepfeatures <- function(object, data, layer = 1) {
              index = layer - 1
              url <- paste0('Predictions/models/', object@model_id, '/frames/', h2o.getId(data))
              res <- .h2o.__remoteSend(url, method = "POST", deep_features_hidden_layer=index, h2oRestApiVersion = 4)
              job_key <- res$key$name
              dest_key <- res$dest$name
              .h2o.__waitOnJob(job_key)
              h2o.getFrame(dest_key)
            }
        """

    if algo == "glm":
        return """
            #' Set betas of an existing H2O GLM Model
            #'
            #' This function allows setting betas of an existing glm model.
            #' @param model an \linkS4class{H2OModel} corresponding from a \code{h2o.glm} call.
            #' @param beta a new set of betas (a named vector)
            #' @export
            h2o.makeGLMModel <- function(model,beta) {
               res = .h2o.__remoteSend(method="POST", .h2o.__GLMMakeModel, model=model@model_id, names = paste("[",paste(paste("\"",names(beta),"\"",sep=""), collapse=","),"]",sep=""), beta = paste("[",paste(as.vector(beta),collapse=","),"]",sep=""))
               m <- h2o.getModel(model_id=res$model_id$name)
               m@model$coefficients <- m@model$coefficients_table[,2]
               names(m@model$coefficients) <- m@model$coefficients_table[,1]
               m
            }

            #' Extract full regularization path from glm model (assuming it was run with lambda search option)
            #'
            #' @param model an \linkS4class{H2OModel} corresponding from a \code{h2o.glm} call.
            #' @export
            h2o.getGLMFullRegularizationPath <- function(model) {
               res = .h2o.__remoteSend(method="GET", .h2o.__GLMRegPath, model=model@model_id)
               colnames(res$coefficients) <- res$coefficient_names
               if(!is.null(res$coefficients_std) && length(res$coefficients_std) > 0L) {
                 colnames(res$coefficients_std) <- res$coefficient_names
               }
               res
            }

            ##' Start an H2O Generalized Linear Model Job
            ##'
            ##' Creates a background H2O GLM job.
            ##' @inheritParams h2o.glm
            ##' @return Returns a \linkS4class{H2OModelFuture} class object.
            ##' @export
            #h2o.startGLMJob <- function(x, y, training_frame, model_id, validation_frame,
            #                    #AUTOGENERATED Params
            #                    max_iterations = 50,
            #                    beta_epsilon = 0,
            #                    solver = c("IRLSM", "L_BFGS"),
            #                    standardize = TRUE,
            #                    family = c("gaussian", "binomial", "poisson", "gamma", "tweedie"),
            #                    link = c("family_default", "identity", "logit", "log", "inverse", "tweedie"),
            #                    tweedie_variance_power = NaN,
            #                    tweedie_link_power = NaN,
            #                    alpha = 0.5,
            #                    prior = 0.0,
            #                    lambda = 1e-05,
            #                    lambda_search = FALSE,
            #                    nlambdas = -1,
            #                    lambda_min_ratio = 1.0,
            #                    nfolds = 0,
            #                    beta_constraints = NULL,
            #                    ...
            #                    )
            #{
            #  # if (!is.null(beta_constraints)) {
            #  #     if (!inherits(beta_constraints, "data.frame") && !is.H2OFrame("H2OFrame"))
            #  #       stop(paste("`beta_constraints` must be an H2OH2OFrame or R data.frame. Got: ", class(beta_constraints)))
            #  #     if (inherits(beta_constraints, "data.frame")) {
            #  #       beta_constraints <- as.h2o(beta_constraints)
            #  #     }
            #  # }
            #
            #  if (!is.H2OFrame(training_frame))
            #      tryCatch(training_frame <- h2o.getFrame(training_frame),
            #               error = function(err) {
            #                 stop("argument \"training_frame\" must be a valid H2OFrame or model ID")
            #              })
            #
            #    parms <- list()
            #    args <- .verify_dataxy(training_frame, x, y)
            #    parms$ignored_columns <- args$x_ignore
            #    parms$response_column <- args$y
            #    parms$training_frame  = training_frame
            #    parms$beta_constraints = beta_constraints
            #    if(!missing(model_id))
            #      parms$model_id <- model_id
            #    if(!missing(validation_frame))
            #      parms$validation_frame <- validation_frame
            #    if(!missing(max_iterations))
            #      parms$max_iterations <- max_iterations
            #    if(!missing(beta_epsilon))
            #      parms$beta_epsilon <- beta_epsilon
            #    if(!missing(solver))
            #      parms$solver <- solver
            #    if(!missing(standardize))
            #      parms$standardize <- standardize
            #    if(!missing(family))
            #      parms$family <- family
            #    if(!missing(link))
            #      parms$link <- link
            #    if(!missing(tweedie_variance_power))
            #      parms$tweedie_variance_power <- tweedie_variance_power
            #    if(!missing(tweedie_link_power))
            #      parms$tweedie_link_power <- tweedie_link_power
            #    if(!missing(alpha))
            #      parms$alpha <- alpha
            #    if(!missing(prior))
            #      parms$prior <- prior
            #    if(!missing(lambda))
            #      parms$lambda <- lambda
            #    if(!missing(lambda_search))
            #      parms$lambda_search <- lambda_search
            #    if(!missing(nlambdas))
            #      parms$nlambdas <- nlambdas
            #    if(!missing(lambda_min_ratio))
            #      parms$lambda_min_ratio <- lambda_min_ratio
            #    if(!missing(nfolds))
            #      parms$nfolds <- nfolds
            #
            #    .h2o.startModelJob('glm', parms, h2oRestApiVersion=.h2o.__REST_API_VERSION)
            #}
        """

def class_extra_for(algo):
    if algo == "deepwater":
        return """
        # Ask the H2O server whether a Deep Water model can be built (depends on availability of native backends)
        #' Returns True if a deep water model can be built, or False otherwise.
        #' @param h2oRestApiVersion (Optional) Specific version of the REST API to use
        #'
        h2o.deepwater.available <- function(h2oRestApiVersion = .h2o.__REST_API_VERSION) {
            visibility = .h2o.__remoteSend(method = "GET", h2oRestApiVersion = h2oRestApiVersion, .h2o.__MODEL_BUILDERS("deepwater"))$model_builders[["deepwater"]][["visibility"]]
            if (visibility == "Experimental") {
                print("Cannot build a Deep Water model - no backend found.")
                return(FALSE)
            } else {
                return(TRUE)
            }
        }
        """
# ----------------------------------------------------------------------------------------------------------------------
#   MAIN:
# ----------------------------------------------------------------------------------------------------------------------
def main():
    bi.init("R", "../../../h2o-r/h2o-package/R", clear_dir=False)

    for name, mb in bi.model_builders().items():
        module = name
        if name == "drf": module = "random_forest"
        if name == "naivebayes": module = "naive_bayes"
        bi.vprint("Generating model: " + name)
        if name == "deepwater" or name == "deeplearning":
            print("Generating model:" + module)
            bi.write_to_file("%s.R" % module, gen_module(mb, name))

if __name__ == "__main__":
    main()