#include <lib/dvb/fbc.h>
#include <lib/dvb/dvb.h>
#include <lib/dvb/sec.h>
#include <lib/base/cfile.h>
#include <lib/base/object.h>

#include <unistd.h>
#include <fcntl.h>

DEFINE_REF(eFBCTunerManager);

eFBCTunerManager* eFBCTunerManager::m_instance = (eFBCTunerManager*)0;

eFBCTunerManager* eFBCTunerManager::getInstance()
{
	return m_instance;
}

eFBCTunerManager::eFBCTunerManager(ePtr<eDVBResourceManager> res_mgr)
	:m_res_mgr(res_mgr)
{
	char tmp[128];
	eSmartPtrList<eDVBRegisteredFrontend> &frontends = m_res_mgr->m_frontend;

	m_instance = this;

	// FIXME
	// This finds the number of virtual tuners even though we want to know
	// the number of physical ("root") tuners. The calculation in the return
	// statement is just a guess and works for now.

	for(m_fbc_tuner_num = 0; m_fbc_tuner_num < 128; m_fbc_tuner_num++)
	{
		snprintf(tmp, sizeof(tmp), "/proc/stb/frontend/%d/fbc_id", m_fbc_tuner_num);

		if(access(tmp, F_OK))
			break;
	}

	/* number of fbc tuners in one set */
	m_fbc_tuner_num /= (FBC_TUNER_SET / 2);

	/* each FBC set has 8 tuners */
	/* first set: 0-7 */
	/* second set: 8-16 */
	/* first, second frontend is top on a set */

	for (eSmartPtrList<eDVBRegisteredFrontend>::iterator it(frontends.begin()); it != frontends.end(); ++it)
		setDefaultFBCID(*it);
}

eFBCTunerManager::~eFBCTunerManager()
{
	m_instance = (eFBCTunerManager*)0;
}

int eFBCTunerManager::fe_slot_id(const eDVBRegisteredFrontend *fe) const
{
	return(fe->m_frontend->getSlotID());
}

long eFBCTunerManager::frontend_get_linkptr(const eDVBRegisteredFrontend *fe, link_ptr_t link_type) const
{
	int data_type;
	long data;

	switch(link_type)
	{
		case(link_prev): data_type = eDVBFrontend::LINKED_PREV_PTR; break;
		case(link_next): data_type = eDVBFrontend::LINKED_NEXT_PTR; break;
		default: return(-1);
	}

	if(fe->m_frontend->getData(data_type, data)) // returns != 0 on error
		data = -1;

	return(data);
}

void eFBCTunerManager::frontend_set_linkptr(const eDVBRegisteredFrontend *fe, link_ptr_t link_type, long data) const
{
	int data_type;

	switch(link_type)
	{
		case(link_prev): data_type = eDVBFrontend::LINKED_PREV_PTR; break;
		case(link_next): data_type = eDVBFrontend::LINKED_NEXT_PTR; break;
		default: return;
	}

	fe->m_frontend->setData(data_type, data);
}

void eFBCTunerManager::setProcFBCID(int fe_id, int fbc_id)
{
	char tmp[64];
	snprintf(tmp, sizeof(tmp), "/proc/stb/frontend/%d/fbc_id", fe_id);

	if(isLinkedByIndex(fe_id))
		fbc_id += 0x10; // 0x10 mask: linked, 0x0f (?) mask: fbc_id // FIXME: shouldn't this be |=?

	CFile::writeIntHex(tmp, fbc_id);
}

bool eFBCTunerManager::isRootFe(eDVBRegisteredFrontend *fe)
{
	return (fe_slot_id(fe) % FBC_TUNER_SET) < m_fbc_tuner_num;
}

bool eFBCTunerManager::isSameFbcSet(int a, int b)
{
	return((a / FBC_TUNER_SET) == (b / FBC_TUNER_SET));
}

int eFBCTunerManager::getFBCID(int top_fe_id)
{
	return (((2 * top_fe_id) / FBC_TUNER_SET) + (top_fe_id % FBC_TUNER_SET)); /* (0,1,8,9,16,17...) -> (0,1,2,3,4,5...) */
}

void eFBCTunerManager::setDefaultFBCID(eDVBRegisteredFrontend *fe)
{
	setProcFBCID(fe_slot_id(fe), isRootFe(fe) ? getFBCID(fe_slot_id(fe)) : 0);
}

void eFBCTunerManager::updateFBCID(eDVBRegisteredFrontend *next_fe, eDVBRegisteredFrontend *prev_fe)
{
	setProcFBCID(fe_slot_id(next_fe), getFBCID(fe_slot_id(getTop(prev_fe))));
}

eDVBRegisteredFrontend *eFBCTunerManager::getPtr(long link)
{
	if(link == -1)
		link = 0;

	return((eDVBRegisteredFrontend *)link);
}

eDVBRegisteredFrontend *eFBCTunerManager::getPrev(eDVBRegisteredFrontend *fe)
{
	long link;

	if((link = frontend_get_linkptr(fe, link_prev)) == -1)
		link = 0;

	return((eDVBRegisteredFrontend *)link);
}

eDVBRegisteredFrontend *eFBCTunerManager::getNext(eDVBRegisteredFrontend *fe)
{
	long link;

	if(!fe)
		return((eDVBRegisteredFrontend *)0);

	if((link = frontend_get_linkptr(fe, link_next)) == -1)
		link = 0;

	return((eDVBRegisteredFrontend *)link);
}

eDVBRegisteredFrontend *eFBCTunerManager::getTop(eDVBRegisteredFrontend *fe)
{
	eDVBRegisteredFrontend *prev_fe;
	long linked_prev_ptr;

	//FIXME: assumed sizeof(*) == sizeof(long)

	for(prev_fe = fe;
			(linked_prev_ptr = frontend_get_linkptr(prev_fe, link_prev)) != -1;
			prev_fe = (eDVBRegisteredFrontend *)linked_prev_ptr)
		(void)0;

	return(prev_fe);
}

eDVBRegisteredFrontend *eFBCTunerManager::getLast(eDVBRegisteredFrontend *fe)
{
	eDVBRegisteredFrontend *next_fe;
	long linked_next_ptr;

	for(next_fe = fe;
			(linked_next_ptr = frontend_get_linkptr(next_fe, link_next)) != -1;
			next_fe = (eDVBRegisteredFrontend *)linked_next_ptr)
		(void)0;

	return(next_fe);
}

bool eFBCTunerManager::isLinked(eDVBRegisteredFrontend *fe)
{
	return(!(getPrev(fe) == (eDVBRegisteredFrontend *)0));
}

bool eFBCTunerManager::isLinkedByIndex(int fe_idx)
{
	bool linked = false;
	eSmartPtrList<eDVBRegisteredFrontend> &frontends = m_res_mgr->m_frontend;

	for (eSmartPtrList<eDVBRegisteredFrontend>::iterator it(frontends.begin()); it != frontends.end(); ++it)
	{
		if (fe_slot_id(it) == fe_idx)
		{
			linked = isLinked(*it);
			break;
		}
	}
	return linked;
}

void eFBCTunerManager::connectLinkNoSimulate(eDVBRegisteredFrontend *link_fe, eDVBRegisteredFrontend *top_fe)
{
	eDVBRegisteredFrontend *last_fe = getLast(top_fe);

	frontend_set_linkptr(last_fe, link_next, (long)link_fe);
	frontend_set_linkptr(link_fe, link_prev, (long)last_fe);

	link_fe->m_frontend->setEnabled(true);

	updateLNBSlotMask(fe_slot_id(link_fe), fe_slot_id(top_fe), false);
}

void eFBCTunerManager::disconnectLinkNoSimulate(eDVBRegisteredFrontend *link_fe)
{
	if(getNext(link_fe))
		return;

	eDVBRegisteredFrontend *prev_fe = getPrev(link_fe);

	if(!prev_fe)
		return;

	frontend_set_linkptr(prev_fe, link_next, -1);
	frontend_set_linkptr(link_fe, link_prev, -1);

	link_fe->m_frontend->setEnabled(false);

	updateLNBSlotMask(fe_slot_id(link_fe), fe_slot_id(prev_fe), true);
}

bool eFBCTunerManager::checkUsed(eDVBRegisteredFrontend *fe, bool a_simulate)
{
	if (fe->m_inuse > 0)
		return true;

	bool simulate = !a_simulate;

	eSmartPtrList<eDVBRegisteredFrontend> &frontends = simulate ? m_res_mgr->m_simulate_frontend : m_res_mgr->m_frontend;

	for (eSmartPtrList<eDVBRegisteredFrontend>::iterator it(frontends.begin()); it != frontends.end(); ++it)
		if (fe_slot_id(it) == fe_slot_id(fe))
			return(it->m_inuse > 0);

	return false;
}

bool eFBCTunerManager::canLink(eDVBRegisteredFrontend *fe)
{
	if(isRootFe(fe))
		return false;

	if(getPrev(fe) || getNext(fe))
		return false;

	if(isUnicable(fe))
		return false;

	return true;
}

bool eFBCTunerManager::isUnicable(eDVBRegisteredFrontend *fe)
{
	ePtr<eDVBSatelliteEquipmentControl> sec = eDVBSatelliteEquipmentControl::getInstance();
	int slot_idx = fe_slot_id(fe);
	bool is_unicable = false;
	int idx;

	for (idx = 0; idx <= sec->m_lnbidx; ++idx)
	{
		eDVBSatelliteLNBParameters &lnb_param = sec->m_lnbs[idx];

		if (lnb_param.m_slot_mask & (1 << slot_idx))
		{
			is_unicable = lnb_param.SatCR_idx != -1;
			break;
		}
	}
	return is_unicable;
}

int eFBCTunerManager::isCompatibleWith(ePtr<iDVBFrontendParameters> &feparm, eDVBRegisteredFrontend *link_fe, eDVBRegisteredFrontend *&fbc_fe, bool simulate)
{
	int best_score = 0;
	int c;

	eSmartPtrList<eDVBRegisteredFrontend> &frontends = simulate ? m_res_mgr->m_simulate_frontend : m_res_mgr->m_frontend;

	for (eSmartPtrList<eDVBRegisteredFrontend>::iterator it(frontends.begin()); it != frontends.end(); ++it)
	{
		if (!it->m_frontend->is_FBCTuner())
			continue;

		if (!isRootFe(*it))
			continue;

		if(!it->m_frontend->getEnabled())
			continue;

		if(!isSameFbcSet(fe_slot_id(link_fe), fe_slot_id(it)))
			continue;

		if(it->m_inuse == 0) // no link to a fe not in use.
			continue;

		if(isLinked(*it)) // no link to a fe linked to another.
			continue;

		if(isUnicable(*it))
			continue;

		connectLinkNoSimulate(link_fe, *it);

		c = link_fe->m_frontend->isCompatibleWith(feparm);

		if (c > best_score)
		{
			best_score = c;
			fbc_fe = (eDVBRegisteredFrontend *)*it;
		}

		disconnectLinkNoSimulate(link_fe);
	}

	return best_score;
}

//FIXME: we should probably do something with simulate and simulate_frontends

void eFBCTunerManager::addLink(eDVBRegisteredFrontend *leaf_fe, eDVBRegisteredFrontend *root_fe, bool simulate)
{
	long leaf_insert_after;
	long leaf_insert_before;
	long leaf_current;
	long leaf_next;

	fprintf(stderr, "\n**** addLink(leaf_fe: %d, link to top fe: %d, simulate: %d\n", fe_slot_id(leaf_fe), fe_slot_id(root_fe), simulate);

	list_loop_links();

	if (!isRootFe(root_fe))
		return;

	// find the entry where to insert the leaf, it must be between slotid(leaf_fe)-1 and slotid(leaf_fe)+1

	leaf_insert_after = -1;
	leaf_insert_before = -1;

	for(leaf_current = (long)root_fe; leaf_current != -1; leaf_current = leaf_next)
	{
		leaf_next = frontend_get_linkptr(getPtr(leaf_current), link_next);

		leaf_insert_after = leaf_current;
		leaf_insert_before = leaf_next;

		if((leaf_next != -1) && (fe_slot_id(getPtr(leaf_next)) > fe_slot_id(leaf_fe)))
			break;
	}

	frontend_set_linkptr(leaf_fe, link_prev, leaf_insert_after);
	frontend_set_linkptr(leaf_fe, link_next, leaf_insert_before);
	frontend_set_linkptr(getPtr(leaf_insert_after), link_next, (long)leaf_fe);

	if(leaf_insert_before != -1) // connect leaf after us in
		frontend_set_linkptr(getPtr(leaf_insert_before), link_prev, (long)leaf_fe);

	leaf_fe->m_frontend->setEnabled(true);

	setProcFBCID(fe_slot_id(leaf_fe), getFBCID(fe_slot_id(root_fe)));
	updateLNBSlotMask(fe_slot_id(leaf_fe), fe_slot_id(root_fe), /*remove*/false);

	list_loop_links();
}

void eFBCTunerManager::unlink(eDVBRegisteredFrontend *fe)
{
	long leaf_link_next;
	long leaf_link_prev;

//FIXME: we should probably do something with simulate and simulate_frontends
	bool simulate = fe->m_frontend->is_simulate();

	list_loop_links();

	if (isRootFe(fe) || checkUsed(fe, simulate) || isUnicable(fe))
		return;

	leaf_link_prev = frontend_get_linkptr(fe, link_prev);
	leaf_link_next = frontend_get_linkptr(fe, link_next);

	if(leaf_link_prev != -1)
		frontend_set_linkptr(getPtr(leaf_link_prev), link_next, leaf_link_next);

	if(leaf_link_next != -1)
		frontend_set_linkptr(getPtr(leaf_link_next), link_prev, leaf_link_prev);

	frontend_set_linkptr(fe, link_prev, -1);
	frontend_set_linkptr(fe, link_next, -1);
	fe->m_frontend->setEnabled(false);

	list_loop_links();

	setProcFBCID(fe_slot_id(fe), 0);
	updateLNBSlotMask(fe_slot_id(fe), fe_slot_id(getTop(fe)), /*remove*/true);
}

int eFBCTunerManager::updateLNBSlotMask(int dest_slot, int src_slot, bool remove)
{
	int idx;
	ePtr<eDVBSatelliteEquipmentControl> sec = eDVBSatelliteEquipmentControl::getInstance();

	int sec_lnbidx = sec->m_lnbidx;

	for (idx = 0; idx <= sec_lnbidx; ++idx)
	{
		eDVBSatelliteLNBParameters &lnb_param = sec->m_lnbs[idx];

		if (lnb_param.m_slot_mask & (1 << src_slot))
		{
			if (!remove)
				lnb_param.m_slot_mask |= (1 << dest_slot);
			else
				lnb_param.m_slot_mask &= ~(1 << dest_slot);
		}
	}

	return 0;
}

int eFBCTunerManager::getLinkedSlotID(int fe_id)
{
	eDVBRegisteredFrontend *prev_fe;
	eSmartPtrList<eDVBRegisteredFrontend> &frontends = m_res_mgr->m_frontend;
	int link;
	long prev_ptr;

	prev_fe = 0;
	link = -1;

	for (eSmartPtrList<eDVBRegisteredFrontend>::iterator it(frontends.begin()); it != frontends.end(); ++it)
	{
		if(it->m_frontend->getSlotID() == fe_id)
		{
			if((prev_ptr = frontend_get_linkptr(it, link_prev)) != -1)
			{
				prev_fe = (eDVBRegisteredFrontend *)prev_ptr;
				link = fe_slot_id(prev_fe);
			}
			break;
		}
	}

	return link;
}

void eFBCTunerManager::list_loop_links(void)
{
	long prev_ptr, next_ptr;
	eSmartPtrList<eDVBRegisteredFrontend> &frontends = m_res_mgr->m_frontend;

	fprintf(stderr, "---- links\n");

	for (eSmartPtrList<eDVBRegisteredFrontend>::iterator it(frontends.begin()); it != frontends.end(); ++it)
	{
		fprintf(stderr, "    tuner %d, prev_links: ", it->m_frontend->getSlotID());

		prev_ptr = frontend_get_linkptr(it, link_prev);

		while(prev_ptr != -1)
		{
			fprintf(stderr, "%d, ", getPtr(prev_ptr)->m_frontend->getSlotID());
			prev_ptr = frontend_get_linkptr(getPtr(prev_ptr), link_prev);
		}

		fprintf(stderr, ", next_links: ");

		next_ptr = frontend_get_linkptr(it, link_next);

		while(next_ptr != -1)
		{
			fprintf(stderr, "%d, ", getPtr(next_ptr)->m_frontend->getSlotID());
			next_ptr = frontend_get_linkptr(getPtr(next_ptr), link_next);
		}

		fprintf(stderr, "\n");
	}

	fprintf(stderr, "++++ links\n");
}
