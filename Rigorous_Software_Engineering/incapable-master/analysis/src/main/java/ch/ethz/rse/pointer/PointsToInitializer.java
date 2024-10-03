package ch.ethz.rse.pointer;

import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.collect.HashMultimap;
import com.google.common.collect.Multimap;

import apron.Texpr1Node;
import ch.ethz.rse.utils.Constants;
import soot.Local;
import soot.SootClass;
import soot.SootMethod;
import soot.Unit;
import soot.Value;
import soot.jimple.IntConstant;
import soot.jimple.InvokeExpr;
import soot.jimple.SpecialInvokeExpr;
import soot.jimple.internal.JInvokeStmt;
import soot.jimple.internal.JSpecialInvokeExpr;
import soot.jimple.internal.JimpleLocal;
import soot.jimple.spark.pag.Node;

/**
 * Convenience class which helps determine the {@link StoreInitializer}s
 * potentially used to create objects pointed to by a given variable
 */
public class PointsToInitializer {

	private static final Logger logger = LoggerFactory.getLogger(PointsToInitializer.class);


	/**
	 * Internally used points-to analysis
	 */
	private final PointsToAnalysisWrapper pointsTo;

	/**
	 * class for which we are running points-to
	 */
	private final SootClass c;

	/**
	 * Maps abstract object indices to initializers
	 */
	private final Map<Node, StoreInitializer> initializers = new HashMap<Node, StoreInitializer>();

	/**
	 * All {@link StoreInitializer}s, keyed by method
	 */
	private final Multimap<SootMethod, StoreInitializer> perMethod = HashMultimap.create();

	public PointsToInitializer(SootClass c) {
		this.c = c;
		logger.debug("Running points-to analysis on " + c.getName());
		this.pointsTo = new PointsToAnalysisWrapper(c);
		logger.debug("Analyzing initializers in " + c.getName());
		this.analyzeAllInitializers();
	}

	private void analyzeAllInitializers() {
		for (SootMethod method : this.c.getMethods()) {

			if (method.getName().contains("<init>")) {
				// skip constructor of the class
				continue;
			}			
			// populate data structures perMethod and initializers
			// TODO: FILL THIS OUT Filled (finished?)
			int uniqueNumber = 0;
			for (Unit unit : method.getActiveBody().getUnits()) {
				logger.debug("Points to Unit " + unit.toString());
				if (unit instanceof JInvokeStmt) {
					//Either new delivery (JVirtualInvokeSExpr) or new Store (JSpecialInvokeExpr)
					JInvokeStmt invokeStmt = (JInvokeStmt) unit;
					logger.debug("invokestatement "+ invokeStmt.toString());
					if(invokeStmt.getInvokeExpr() instanceof JSpecialInvokeExpr){
						JSpecialInvokeExpr sInvokeExpr = (JSpecialInvokeExpr) invokeStmt.getInvokeExpr();
						logger.debug("sInvokeExpr "+ sInvokeExpr);
						Value v0 = sInvokeExpr.getArg(0);
						Value v1 = sInvokeExpr.getArg(1);
						//according to the task implementation tipps v0 and v1 are only integer constants (Soot.jimple.IntConstant) so we can cast
						int trolley_size = ((IntConstant) v0).value;
						int reserve_size = ((IntConstant) v1).value;	
						
						StoreInitializer storeInitializer = new StoreInitializer(invokeStmt, uniqueNumber++, trolley_size, reserve_size);
						perMethod.put(method,storeInitializer);
						
						Collection<Node> allocationNodes = getAllocationNodes(sInvokeExpr);
						for (Node node : allocationNodes) {
							initializers.put(node, storeInitializer);
						}

						
					}
				}
			}
		}
	}


	public Collection<StoreInitializer> getInitializers(SootMethod method) {
		return this.perMethod.get(method);
	}

	public List<StoreInitializer> pointsTo(Local base) {
		Collection<Node> nodes = this.pointsTo.getNodes(base);
		List<StoreInitializer> initializers = new LinkedList<StoreInitializer>();
		for (Node node : nodes) {
			StoreInitializer initializer = this.initializers.get(node);
			if (initializer != null) {
				// ignore nodes that were not initialized
				initializers.add(initializer);
			}
		}
		return initializers;
	}

	/**
	 * Returns all allocation nodes that could correspond to the given invokeExpression, which must be a call to Store init function
	 * Note that more than one node can be returned.
	 */
	public Collection<Node> getAllocationNodes(JSpecialInvokeExpr invokeExpr){
		if(!isRelevantInit(invokeExpr)){
			throw new RuntimeException("Call to getAllocationNodes with " + invokeExpr.toString() + "which is not an init call for the Store class");
		}
		Local base = (Local) invokeExpr.getBase();
		Collection<Node> allocationNodes = this.pointsTo.getNodes(base);
		return allocationNodes;
	}

	public boolean isRelevantInit(JSpecialInvokeExpr invokeExpr){
		Local base = (Local) invokeExpr.getBase();
		boolean isRelevant = base.getType().toString().equals(Constants.StoreClassName);
		boolean isInit = invokeExpr.getMethod().getName().equals("<init>");
		return isRelevant && isInit;
	}
}
