package ch.ethz.rse.numerical;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import apron.Abstract1;
import apron.ApronException;
import apron.Environment;
import apron.Manager;
import apron.MpqScalar;
import apron.Polka;
import apron.Tcons1;
import apron.Texpr1BinNode;
import apron.Texpr1CstNode;
import apron.Texpr1Intern;
import apron.Texpr1Node;
import apron.Texpr1VarNode;
import ch.ethz.rse.VerificationProperty;
import ch.ethz.rse.VerificationResult;
import ch.ethz.rse.pointer.StoreInitializer;
import ch.ethz.rse.pointer.PointsToInitializer;
import ch.ethz.rse.utils.Constants;
import ch.ethz.rse.verify.EnvironmentGenerator;
import ch.qos.logback.core.joran.conditional.Condition;
import gmp.Mpq;
import heros.solver.Pair;
import jas.Base64;
import soot.ArrayType;
import soot.DoubleType;
import soot.Local;
import soot.RefType;
import soot.SootHelper;
import soot.SootMethod;
import soot.Unit;
import soot.Value;
import soot.jimple.AddExpr;
import soot.jimple.BinopExpr;
import soot.jimple.ConditionExpr;
import soot.jimple.DefinitionStmt;
import soot.jimple.IfStmt;
import soot.jimple.IntConstant;
import soot.jimple.InvokeExpr;
import soot.jimple.Jimple;
import soot.jimple.MulExpr;
import soot.jimple.ParameterRef;
import soot.jimple.Stmt;
import soot.jimple.SubExpr;
import soot.jimple.internal.AbstractBinopExpr;
import soot.jimple.internal.JAddExpr;
import soot.jimple.internal.JArrayRef;
import soot.jimple.internal.JEqExpr;
import soot.jimple.internal.JGeExpr;
import soot.jimple.internal.JGotoStmt;
import soot.jimple.internal.JGtExpr;
import soot.jimple.internal.JIfStmt;
import soot.jimple.internal.JInstanceFieldRef;
import soot.jimple.internal.JInvokeStmt;
import soot.jimple.internal.JLeExpr;
import soot.jimple.internal.JLtExpr;
import soot.jimple.internal.JMulExpr;
import soot.jimple.internal.JNeExpr;
import soot.jimple.internal.JReturnVoidStmt;
import soot.jimple.internal.JSpecialInvokeExpr;
import soot.jimple.internal.JSubExpr;
import soot.jimple.internal.JVirtualInvokeExpr;
import soot.jimple.internal.JimpleLocal;
import soot.jimple.toolkits.annotation.logic.Loop;
import soot.toolkits.graph.LoopNestTree;
import soot.toolkits.graph.UnitGraph;
import soot.toolkits.scalar.ForwardBranchedFlowAnalysis;
import soot.jimple.internal.JIdentityStmt;

/**
 * Convenience class running a numerical analysis on a given {@link SootMethod}
 */
public class NumericalAnalysis extends ForwardBranchedFlowAnalysis<NumericalStateWrapper> {

	private static final Logger logger = LoggerFactory.getLogger(NumericalAnalysis.class);

	/**
	 * Those properties return our result
	 **/
	private VerificationResult non_Negative_Res;
	private VerificationResult Fits_In_Reserve_Res;
	private VerificationResult Fits_In_Trolley_Res;

	private final SootMethod method;

	public HashMap<Local, ArrayList<Texpr1Node>> reserve_Map = new HashMap<Local, ArrayList<Texpr1Node>>();
	public HashMap<Local, ArrayList<NumericalStateWrapper>> wrapper_Map = new HashMap<Local, ArrayList<NumericalStateWrapper>>();

	/**
	 * the property we are verifying
	 */
	private final VerificationProperty property;

	/**
	 * the pointer analysis result we are verifying
	 */
	private final PointsToInitializer pointsTo;

	/**
	 * all store initializers encountered until now
	 */
	private Set<StoreInitializer> alreadyInit;

	/**
	 * number of times this loop head was encountered during analysis
	 */
	private HashMap<Unit, IntegerWrapper> loopHeads = new HashMap<Unit, IntegerWrapper>();
	/**
	 * Previously seen abstract state for each loop head o
	 */
	private HashMap<Unit, NumericalStateWrapper> loopHeadState = new HashMap<Unit, NumericalStateWrapper>();

	/**
	 * Numerical abstract domain to use for analysis: Convex polyhedra
	 */
	public final Manager man = new Polka(true);

	public final Environment env;

	/**
	 * We apply widening after updating the state at a given merge point for the
	 * {@link WIDENING_THRESHOLD}th time
	 */
	private static final int WIDENING_THRESHOLD = 6;

	/**
	 * 
	 * @param method   method to analyze
	 * @param property the property we are verifying
	 */
	public NumericalAnalysis(SootMethod method, VerificationProperty property, PointsToInitializer pointsTo) {
		super(SootHelper.getUnitGraph(method));

	

		UnitGraph g = SootHelper.getUnitGraph(method);

		this.property = property;

		this.pointsTo = pointsTo;

		this.method = method;

		this.alreadyInit = new HashSet<StoreInitializer>();

		this.env = new EnvironmentGenerator(method, pointsTo).getEnvironment();

		// initialize counts for loop heads
		for (Loop l : new LoopNestTree(g.getBody())) {
			loopHeads.put(l.getHead(), new IntegerWrapper(0));
		}

		// perform analysis by calling into super-class
		logger.info("Analyzing {} in {}", method.getName(), method.getDeclaringClass().getName());
		doAnalysis(); // calls newInitialFlow, entryInitialFlow, merge, flowThrough, and stops when a
						// fixed point is reached
	}

	/**
	 * Report unhandled instructions, types, cases, etc.
	 * 
	 * @param task description of current task
	 * @param what
	 */
	public static void unhandled(String task, Object what, boolean raiseException) {
		String description = task + ": Can't handle " + what.toString() + " of type " + what.getClass().getName();

		if (raiseException) {
			logger.error("Raising exception " + description);
			throw new UnsupportedOperationException(description);
		} else {
			logger.error(description);

			// print stack trace
			StackTraceElement[] stackTrace = Thread.currentThread().getStackTrace();
			for (int i = 1; i < stackTrace.length; i++) {
				logger.error(stackTrace[i].toString());
			}
		}
	}

	@Override
	protected void copy(NumericalStateWrapper source, NumericalStateWrapper dest) {
		source.copyInto(dest);
	}

	@Override
	protected NumericalStateWrapper newInitialFlow() {
		// should be bottom (only entry flows are not bottom originally)
		return NumericalStateWrapper.bottom(man, env);
	}

	@Override
	protected NumericalStateWrapper entryInitialFlow() {
		// state of entry points into function
		NumericalStateWrapper ret = NumericalStateWrapper.top(man, env);

		// TODO: MAYBE FILL THIS OUT

		return ret;
	}

	@Override
	protected void merge(Unit succNode, NumericalStateWrapper w1, NumericalStateWrapper w2, NumericalStateWrapper w3) {
		// merge the two states from w1 and w2 and store the result into w3
		logger.debug("in merge: " + succNode);

		try {
			w3.set(w1.get().joinCopy(this.man, w2.get()));
		} catch (Exception e) {
			e.printStackTrace();
		}

		// TODO: OK FILL THIS OUT
	}

	@Override
	protected void merge(NumericalStateWrapper src1, NumericalStateWrapper src2, NumericalStateWrapper trg) {
		// this method is never called, we are using the other merge instead
		throw new UnsupportedOperationException();
	}

	@Override
	protected void flowThrough(NumericalStateWrapper inWrapper, Unit op, List<NumericalStateWrapper> fallOutWrappers,
			List<NumericalStateWrapper> branchOutWrappers) {
		logger.debug(inWrapper + " " + op + " => ?");
		logger.debug("Operation "+op);
		Stmt s = (Stmt) op;

		// fallOutWrapper is the wrapper for the state after running op,
		// assuming we move to the next statement. Do not overwrite
		// fallOutWrapper, but use its .set method instead
		assert fallOutWrappers.size() <= 1;
		NumericalStateWrapper fallOutWrapper = null;
		if (fallOutWrappers.size() == 1) {
			fallOutWrapper = fallOutWrappers.get(0);
			inWrapper.copyInto(fallOutWrapper);
		}

		// branchOutWrapper is the wrapper for the state after running op,
		// assuming we follow a conditional jump. It is therefore only relevant
		// if op is a conditional jump. In this case, (i) fallOutWrapper
		// contains the state after "falling out" of the statement, i.e., if the
		// condition is false, and (ii) branchOutWrapper contains the state
		// after "branching out" of the statement, i.e., if the condition is
		// true.
		assert branchOutWrappers.size() <= 1;
		NumericalStateWrapper branchOutWrapper = null;
		if (branchOutWrappers.size() == 1) {
			branchOutWrapper = branchOutWrappers.get(0);
			inWrapper.copyInto(branchOutWrapper);
		}

		try {
			if (s instanceof DefinitionStmt) {
				// handle assignment

				DefinitionStmt sd = (DefinitionStmt) s;
				logger.debug(sd.toString() + " case");
				Value left = sd.getLeftOp();
				Value right = sd.getRightOp();

				// We are not handling these cases:
				if (!(left instanceof JimpleLocal)) {
					unhandled("Assignment to non-local variable", left, true);
				} else if (left instanceof JArrayRef) {
					unhandled("Assignment to a non-local array variable", left, true);
				} else if (left.getType() instanceof ArrayType) {
					unhandled("Assignment to Array", left, true);
				} else if (left.getType() instanceof DoubleType) {
					unhandled("Assignment to double", left, true);
				} else if (left instanceof JInstanceFieldRef) {
					unhandled("Assignment to field", left, true);
				}

				if (left.getType() instanceof RefType) {
					// assignments to references are handled by pointer analysis
					// no action necessary
					logger.debug("case reftype " + left.toString() + " " + right.toString());
					// } else if (s instanceof JIdentityStmt) {
					// nothing
				} else {
					// handle assignment
					logger.debug("case handledef");
					handleDef(fallOutWrapper, left, right);
				}

				// TODO not sure why we need this -> with this parameter works
				// }

			} else if (s instanceof JIfStmt) {
				// handling if statemants in the test file

				// TODO: FILL THIS OUT Started
				JIfStmt jIfStmt = (JIfStmt) s;
				logger.debug(jIfStmt.toString() + " case");
				// cond is a Value (more correctly a ConditionExpr) of the form e.g. a<=2
				Value cond = jIfStmt.getCondition();

				// Value left and right describe the two variables/numbers of the expression -
				// as evaluated expression nodes
				// Value left = ((ConditionExpr) cond).getOp1();
				// Value right = ((ConditionExpr) cond).getOp2();

				Texpr1Node left = evalExpr(((ConditionExpr) cond).getOp1());
				Texpr1Node right = evalExpr(((ConditionExpr) cond).getOp2());

				// Workflow:
				// Get constraints for the given Condition
				// Add Constraints to the specific Wrappers
				// Meet the Wrappers

				Tcons1 branchConstraint = null;
				Tcons1 falloutConstraint = null;

				if (cond instanceof JEqExpr) {
					branchConstraint = new Tcons1(env, Tcons1.EQ, new Texpr1BinNode(Texpr1BinNode.OP_SUB, left, right));
					falloutConstraint = new Tcons1(env, Tcons1.DISEQ,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, left, right));
				} else if (cond instanceof JGeExpr) {
					branchConstraint = new Tcons1(env, Tcons1.SUPEQ,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, left, right));
					falloutConstraint = new Tcons1(env, Tcons1.SUP,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, right, left));
				} else if (cond instanceof JGtExpr) {
					branchConstraint = new Tcons1(env, Tcons1.SUP,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, left, right));
					falloutConstraint = new Tcons1(env, Tcons1.SUPEQ,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, right, left));
				} else if (cond instanceof JLeExpr) {
					branchConstraint = new Tcons1(env, Tcons1.SUPEQ,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, right, left));
					falloutConstraint = new Tcons1(env, Tcons1.SUP,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, left, right));
				} else if (cond instanceof JLtExpr) {
					branchConstraint = new Tcons1(env, Tcons1.SUP,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, right, left));
					falloutConstraint = new Tcons1(env, Tcons1.SUPEQ,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, left, right));
				} else if (cond instanceof JNeExpr) {
					branchConstraint = new Tcons1(env, Tcons1.DISEQ,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, right, left));
					falloutConstraint = new Tcons1(env, Tcons1.EQ,
							new Texpr1BinNode(Texpr1BinNode.OP_SUB, left, right));
				}

				logger.debug("nici cond1" + cond);

				boolean widening = false;

				try {
					int iteration = loopHeads.get(op).value;
					logger.debug("iteration: " + iteration);
					if (iteration >= WIDENING_THRESHOLD) {
						Abstract1 join1 = branchOutWrapper.get().joinCopy(man, loopHeadState.get(op).get());
						branchOutWrapper.set(loopHeadState.get(op).get().widening(man, join1));
						branchOutWrappers.set(0, branchOutWrapper);

						Abstract1 join2 = fallOutWrapper.get().joinCopy(man, loopHeadState.get(op).get());
						fallOutWrapper.set(loopHeadState.get(op).get().widening(man, join2));
						logger.debug("fallout iteration: " + fallOutWrapper);
						fallOutWrappers.set(0, fallOutWrapper);

						widening = true;
						logger.debug("widening true");
					}
					loopHeadState.put(op, inWrapper.copy());
					loopHeads.get(op).value++;
				} catch (Exception e) {
					logger.debug("Not a Loop head");
				}

				logger.debug("nici branch" + branchOutWrapper);
				logger.debug("nici fall" + fallOutWrapper);

				logger.debug("nici constraint" + branchConstraint);
				logger.debug("nici constraint" + falloutConstraint);
				if (!widening) {
					Abstract1 elem1 = branchOutWrapper.get();
					Abstract1 elem2 = fallOutWrapper.get();

					branchOutWrapper.set(elem1.meetCopy(man, branchConstraint));
					fallOutWrapper.set(elem2.meetCopy(man, falloutConstraint));
				}

				logger.debug("nici branch" + branchOutWrapper);
				logger.debug("nici fall" + fallOutWrapper);
				// TODO: perform Widening

			} else if (s instanceof JInvokeStmt) {
				// handle invocations
				JInvokeStmt jInvStmt = (JInvokeStmt) s;
				InvokeExpr invokeExpr = jInvStmt.getInvokeExpr();

				if (invokeExpr instanceof JVirtualInvokeExpr) {
					logger.debug("jInvStmt handleInvoke Iteration"+ jInvStmt);
					handleInvoke(jInvStmt, fallOutWrapper);
				} else if (invokeExpr instanceof JSpecialInvokeExpr) {
					// initializer for object
					handleInitialize(jInvStmt, fallOutWrapper);
				} else {
					unhandled("Unhandled invoke statement", invokeExpr, true);
				}
			} else if (s instanceof JGotoStmt) {
				// safe to ignore
			} else if (s instanceof JReturnVoidStmt) {
				// safe to ignore
			} else {
				unhandled("Unhandled statement", s, true);
			}

			// log outcome
			if (fallOutWrapper != null) {
				logger.debug(inWrapper.get() + " " + s + " =>[fallout] " + fallOutWrapper);
			}
			if (branchOutWrapper != null) {
				logger.debug(inWrapper.get() + " " + s + " =>[branchout] " + branchOutWrapper);
			}

		} catch (ApronException e) {
			throw new RuntimeException(e);
		}
	}

	public Texpr1Node evalExpr(Value v) {
		logger.debug("evaluating expression: " + v);
		if (v instanceof AddExpr) {
			return handleBinOp(((JAddExpr) v).getOp1(), ((JAddExpr) v).getOp2(), Texpr1BinNode.OP_ADD);
		}
		if (v instanceof MulExpr) {
			return handleBinOp(((JMulExpr) v).getOp1(), ((JMulExpr) v).getOp2(), Texpr1BinNode.OP_MUL);
		}
		if (v instanceof SubExpr) {
			return handleBinOp(((JSubExpr) v).getOp1(), ((JSubExpr) v).getOp2(), Texpr1BinNode.OP_SUB);
		}
		if (v instanceof IntConstant) {
			MpqScalar scalarRightValue = new MpqScalar(((IntConstant) v).value);
			return new Texpr1CstNode(scalarRightValue);
		}
		if (v instanceof JimpleLocal) {
			return new Texpr1VarNode(((JimpleLocal) v).getName());
		}
		return null;
	}

	/**
	 * This Method handles the main logic behind our programm, it distinguishes
	 * between the different Verification Properties
	 * and adds a result to the variable non_Negative_Res, Fits_In_Trolley_Res or
	 * Fits_In_Reserve_Res respectively
	 * 
	 * @param jInvStmt       corresponds to a neew delivery (JVirtualInvokeExpr)
	 * @param fallOutWrapper corresponds to the current state of all variable
	 * @throws ApronException Idk
	 */
	public void handleInvoke(JInvokeStmt jInvStmt, NumericalStateWrapper fallOutWrapper) throws ApronException {
		// JInvStmt is a new delivery made (JVirtualInvokeExpr) so we need to check the
		// three properties for that delivery, if it is reachable

		JVirtualInvokeExpr delivery = (JVirtualInvokeExpr) jInvStmt.getInvokeExpr();
		Value deliverySize = delivery.getArg(0);
		logger.debug("Delivery Size " + deliverySize);
		Texpr1Node delSizeNode = generateTexprNode(deliverySize);
		logger.debug("Delivery Size Node " + delSizeNode);
		if (this.property.equals(VerificationProperty.NON_NEGATIVE)) {
			Tcons1 nonNegative = new Tcons1(env, Tcons1.SUPEQ, delSizeNode);
			logger.debug("nici" + nonNegative.toString());
			// If the VerificationResult NonNegative already is false we want to leave it,
			// otherwise make a new one with false or true
			if (non_Negative_Res == null || non_Negative_Res.isSafe) {
				logger.debug("ok" + fallOutWrapper.get().satisfy(man, nonNegative));
				non_Negative_Res = new VerificationResult(fallOutWrapper.get().satisfy(man, nonNegative));
				logger.debug("Falloutwrapper " + fallOutWrapper.get());
			}

		}
		if (this.property == VerificationProperty.FITS_IN_TROLLEY) {
			Value base = delivery.getBase(); // Base is the variable the delivery is assigned to
			List<StoreInitializer> assignedStores = this.pointsTo.pointsTo((JimpleLocal) base);
			int minSize = Integer.MAX_VALUE;
			for (StoreInitializer storeInitializer : assignedStores) { // for all assigned stores find the minimum
																		// trolly size
				minSize = Integer.min(minSize, storeInitializer.getTrolleySize());
			}
			// In this block we check minSize-deliverySize>0
			Texpr1CstNode trolleySize = new Texpr1CstNode(new MpqScalar(minSize));
			Texpr1BinNode trolleyMinusDelivery = new Texpr1BinNode(Texpr1BinNode.OP_SUB, trolleySize, delSizeNode);
			Texpr1Intern internExpr = new Texpr1Intern(env, trolleyMinusDelivery);
			Tcons1 trolleyCons = new Tcons1(Tcons1.SUPEQ, internExpr);
			if (Fits_In_Trolley_Res == null || Fits_In_Trolley_Res.isSafe) {
				Fits_In_Trolley_Res = new VerificationResult(fallOutWrapper.get().satisfy(man, trolleyCons));
			}
			// Tcons1 trolleySize = new Tcons1(env,Tcons1.SUPEQ,minSize);

		}
		/*
		 * To add multiple things together we handle it in the verifyier. Therefore we
		 * populate a Map that maps our
		 * delverySizeNode to the corresponding fallOutWrapper
		 */
		if (this.property == VerificationProperty.FITS_IN_RESERVE) {
			Texpr1Node copyDelSize = delSizeNode.clone();
			logger.debug("DeliverySize" +copyDelSize);
			logger.debug("DeliveryBase" + delivery.getBase());
			logger.debug("falloutwrapper bottom" +fallOutWrapper);
			if (!reserve_Map.containsKey((JimpleLocal) delivery.getBase()))
				reserve_Map.put((JimpleLocal) delivery.getBase(), new ArrayList<Texpr1Node>());
			reserve_Map.get((JimpleLocal) delivery.getBase()).add(copyDelSize);
			if (!wrapper_Map.containsKey((JimpleLocal) delivery.getBase()))
				wrapper_Map.put((JimpleLocal) delivery.getBase(), new ArrayList<NumericalStateWrapper>());
			wrapper_Map.get((JimpleLocal) delivery.getBase()).add(fallOutWrapper.copy());
			logger.debug("Wrappermap"+ wrapper_Map.get((JimpleLocal) delivery.getBase()));
		}

	}

	public void handleInitialize(JInvokeStmt jInvStmt, NumericalStateWrapper fallOutWrapper) throws ApronException {
		// not needed because we dont have to check any properties about the constructor
		// (can be any int, also negative)
		// TODO: MAYBE FILL THIS OUT
	}

	// returns state of in after assignment
	private void handleDef(NumericalStateWrapper outWrapper, Value left, Value right) throws ApronException {
		// DONE: TODO: FILL THIS OUT
		if (right instanceof ParameterRef) {
			return;
		}
		Abstract1 elem = outWrapper.get();
		Texpr1Node exprNode = generateTexprNode(right);
		Texpr1Intern intern = new Texpr1Intern(env, exprNode);
		Abstract1 afterAssignment = elem.assignCopy(man, ((JimpleLocal) left).getName(), intern, null);
		outWrapper.set(afterAssignment);
	}

	private Texpr1Node generateTexprNode(Value right) {
		logger.debug("TODOwiesonullpointers " + right.getType().toString());
		if (right instanceof JimpleLocal) {
			return new Texpr1VarNode(((JimpleLocal) right).getName());
		} else if (right instanceof IntConstant) {
			logger.debug("TODOwieso");
			MpqScalar scalarRightValue = new MpqScalar(((IntConstant) right).value);
			return new Texpr1CstNode(scalarRightValue);
		} else if (right instanceof JMulExpr) {
			return handleBinOp(((BinopExpr) right).getOp1(), ((BinopExpr) right).getOp2(), Texpr1BinNode.OP_MUL);
		} else if (right instanceof JAddExpr) {
			return handleBinOp(((BinopExpr) right).getOp1(), ((BinopExpr) right).getOp2(), Texpr1BinNode.OP_ADD);
		} else if (right instanceof JSubExpr) {
			return handleBinOp(((BinopExpr) right).getOp1(), ((BinopExpr) right).getOp2(), Texpr1BinNode.OP_SUB);
		} else if (right instanceof ParameterRef) {
			logger.debug("TODO");
			// return new Texpr1VarNode(((JimpleLocal)right).getName());
		}
		return null;
	}

	private Texpr1Node handleBinOp(Value op1, Value op2, int operation) {
		Texpr1Node expr1 = generateTexprNode(op1);
		Texpr1Node expr2 = generateTexprNode(op2);
		return new Texpr1BinNode(operation, Texpr1BinNode.RTYPE_INT, Texpr1BinNode.RDIR_ZERO, expr1, expr2);
	}

	public VerificationProperty gProperty() {
		return this.property;
	}

	public boolean verifyProperty() {
		if (non_Negative_Res != null && this.property.equals(VerificationProperty.NON_NEGATIVE))
			return non_Negative_Res.isSafe;
		if (Fits_In_Reserve_Res != null && this.property.equals(VerificationProperty.FITS_IN_RESERVE))
			return Fits_In_Reserve_Res.isSafe;
		if (Fits_In_Trolley_Res != null && this.property.equals(VerificationProperty.FITS_IN_TROLLEY))
			return Fits_In_Trolley_Res.isSafe;
		logger.debug("Hello world");
		return true;
	}
}
