#' Online alignment of LC-MS files
#'
#' Online alignment of LC-MS files
#'
#' Online alignment of LC-MS files
#'
#' @docType package
#' @importFrom gghighlight gghighlight
#' @import viridis
#' @import rtree
#' @import Rcpp
#' @import xcms
#' @importFrom BiocParallel bplapply bpmapply bpparam
#' @importFrom stringr str_split fixed
#' @importFrom tools md5sum
#' @importFrom Matrix Matrix
#' @import xcms
#' @importFrom ClusterR GMM
#' @importFrom data.table fread fwrite as.data.table
#' @importFrom lpSolve lp.transport
#' @useDynLib onlineLCMSaligner, .registration = TRUE 
#' @name onlineLCMSaligner-package
NULL