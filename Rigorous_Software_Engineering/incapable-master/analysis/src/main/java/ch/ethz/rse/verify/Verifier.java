package ch.ethz.rse.verify;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import apron.ApronException;
import apron.MpqScalar;
import apron.Tcons1;
import apron.Texpr1BinNode;
import apron.Texpr1CstNode;
import apron.Texpr1Intern;
import apron.Texpr1Node;
import apron.Texpr1VarNode;
import ch.ethz.rse.VerificationProperty;
import ch.ethz.rse.numerical.NumericalAnalysis;
import ch.ethz.rse.numerical.NumericalStateWrapper;
import ch.ethz.rse.pointer.StoreInitializer;
import ch.ethz.rse.pointer.PointsToInitializer;
import ch.ethz.rse.utils.Constants;
import fj.data.HashMap;
import heros.solver.Pair;
import polyglot.ast.Call;
import soot.Local;
import soot.SootClass;
import soot.SootHelper;
import soot.SootMethod;
import soot.Unit;
import soot.Value;
import soot.jimple.NumericConstant;
import soot.jimple.internal.JInvokeStmt;
import soot.jimple.internal.JSpecialInvokeExpr;
import soot.jimple.internal.JVirtualInvokeExpr;
import soot.toolkits.graph.UnitGraph;

/**
 * Main class handling verification ok
 * 
 */
public class Verifier extends AVerifier {

	private static final Logger logger = LoggerFactory.getLogger(Verifier.class);

	/**
	 * class to be verified
	 */
	private final SootClass c;

	/**
	 * points to analysis for verified class
	 */
	private final PointsToInitializer pointsTo;

	/**
	 * 
	 * @param c class to verify
	 */
	public Verifier(SootClass c) {
		logger.debug("Analyzing {}", c.getName());

		this.c = c;

		// pointer analysis
		this.pointsTo = new PointsToInitializer(this.c);
	}

	protected void runNumericalAnalysis(VerificationProperty property) {
		// TODO: Started FILL THIS OUT
		for (SootMethod method : c.getMethods()) {
			if (method.getName().contains("<init>")) {
				continue;
				// Will skip over constructor
			}
			UnitGraph graph = SootHelper.getUnitGraph(method);
			logger.debug(graph.toString());
			NumericalAnalysis numAnal = new NumericalAnalysis(method, property, pointsTo);
			this.numericalAnalysis.put(method, numAnal);
		}
	}

	@Override
	public boolean checksNonNegative() {
		// DONE: FILL THIS OUT (TODO)

		logger.debug("numerical analysis " + this.numericalAnalysis.toString());
		for (NumericalAnalysis numericalAnalysis : numericalAnalysis.values()) {
			if (numericalAnalysis.gProperty().equals(VerificationProperty.NON_NEGATIVE) &&
					!numericalAnalysis.verifyProperty()) {
				return false;
			}
		}
		return true;
	}

	@Override
	public boolean checkFitsInTrolley() {
		// DONE: FILL THIS OUT (TODO)
		logger.debug("Executing checkFitsInTrolley in Verifier.java");
		for (NumericalAnalysis numAnal : this.numericalAnalysis.values()) {
			if (numAnal.gProperty().equals(VerificationProperty.FITS_IN_TROLLEY)) {
				if (!numAnal.verifyProperty()) {
					return false;
				}
			}
		}
		return true;
	}

	@Override
	public boolean checkFitsInReserve() {
		logger.debug("Executing checkFitsInReserve in Verifier.java");
		for (NumericalAnalysis numAnal : this.numericalAnalysis.values()) {
			if (numAnal.gProperty().equals(VerificationProperty.FITS_IN_RESERVE)) {
				java.util.HashMap<Local, ArrayList<Texpr1Node>> reserve_Map = numAnal.reserve_Map;
				logger.debug("esse"+ reserve_Map);
				java.util.HashMap<Local, ArrayList<NumericalStateWrapper>> wrapper_Map = numAnal.wrapper_Map;
				logger.debug("esse2"+ wrapper_Map);
				for (Local variable : reserve_Map.keySet()) {
					List<StoreInitializer> assignedStores = this.pointsTo.pointsTo(variable);
					int minSize = Integer.MAX_VALUE;
					for (StoreInitializer storeInitializer : assignedStores) { // for all assigned stores find the
																				// minimum reserve size
						minSize = Integer.min(minSize, storeInitializer.getReserveSize());
					}
					Texpr1CstNode Reserve_Expr = new Texpr1CstNode(new MpqScalar(minSize));
					Texpr1CstNode zero = new Texpr1CstNode(new MpqScalar(0));
					Texpr1BinNode ReserveMinusDelivery = new Texpr1BinNode(Texpr1BinNode.OP_ADD, Reserve_Expr, zero); // not
																														// clean
																														// but
																														// works
					if ((reserve_Map.get(variable) == null || reserve_Map.get(variable).isEmpty()) && minSize >= 0)
						return false;
					if (reserve_Map.get(variable) != null && reserve_Map.get(variable).size() > 0) {
						int i = 0;
						for (Texpr1Node node : reserve_Map.get(variable)) {
							try {
								logger.debug("Variable i = "+i);
								if(!wrapper_Map.get(variable).get(i).get().isBottom(numAnal.man)){
									logger.debug("Vor Minus" + ReserveMinusDelivery);
									ReserveMinusDelivery = new Texpr1BinNode(Texpr1BinNode.OP_SUB, ReserveMinusDelivery, node);
									logger.debug("Nach Minus" + ReserveMinusDelivery);
								}
							} catch (ApronException e) {
								logger.debug("Alarm");
							}
							i++;
						}
						Texpr1Intern ReserveIntern = new Texpr1Intern(numAnal.env, ReserveMinusDelivery);
						Tcons1 ReserveCons = new Tcons1(Tcons1.SUPEQ, ReserveIntern);
						logger.debug("ReserveCons " +ReserveCons);
						NumericalStateWrapper mergedState = NumericalStateWrapper.bottom(numAnal.man, numAnal.env);
						for (NumericalStateWrapper fallOutWrapper : wrapper_Map.get(variable)) { // not sure if this is
																									// necesary
							try {
								logger.debug("FalloutWrapper Verifier "+fallOutWrapper.get());
								logger.debug("Merged shit "+mergedState.get().joinCopy(numAnal.man, fallOutWrapper.get()));
								mergedState.set(mergedState.get().joinCopy(numAnal.man, fallOutWrapper.get()));
								//mergedState.set(mergedState.get().joinCopy(numAnal.man, fallOutWrapper.get()));
								logger.debug("mergedFallout "+ mergedState);
								
							} catch (ApronException e) {
								logger.debug("Alarm");
							}
						}
						try {
							logger.debug("mergedFallout "+mergedState);
							if(!mergedState.get().satisfy(numAnal.man,ReserveCons)) return false;
						} catch (Exception e) {
							logger.debug("Alarm 2");
							return false;
						}
					}
				}
			}
		}
		return true;
	}

	// MAYBE FILL THIS OUT: add convenience methods

}
